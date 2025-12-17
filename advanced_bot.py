"""
Телеграм-бот для парсинга VC-каналов и авторазметки ролей (ментор/инвестор/ангел/основатель/сотрудник).
Работает локально через long-polling и может быть запущен на Vercel через вебхук.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List

import pandas as pd
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from advanced_parser import AdvancedVCParser, load_config
from classifier import VCClassifier
from database import VCDatabase
from scheduler import ParsingScheduler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

services_lock = asyncio.Lock()


def load_bot_token() -> str:
    env_token = os.getenv("BOT_TOKEN")
    if env_token:
        return env_token
    try:
        with open("bot_config.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("bot_token", "")
    except FileNotFoundError:
        return ""


async def build_services(enable_scheduler: bool = True) -> Dict:
    parser_config = load_config()
    if not parser_config:
        raise RuntimeError("Не удалось загрузить config.json или переменные окружения.")

    parser = AdvancedVCParser(
        api_id=parser_config["api_id"],
        api_hash=parser_config["api_hash"],
        phone=parser_config["phone"],
        session_string=parser_config.get("session_string"),
    )
    await parser.connect()

    classifier = VCClassifier()
    database = VCDatabase()
    scheduler = ParsingScheduler(parser, classifier, database, enabled=enable_scheduler)
    await scheduler.start()

    logger.info("Сервисы парсера и классификатора готовы.")
    return {
        "parser": parser,
        "classifier": classifier,
        "database": database,
        "scheduler": scheduler,
        "parser_config": parser_config,
    }


async def ensure_services(application: Application) -> Dict:
    async with services_lock:
        services = application.bot_data.get("services")
        if services:
            return services
        enable_scheduler = application.bot_data.get("enable_scheduler", True)
        services = await build_services(enable_scheduler=enable_scheduler)
        application.bot_data["services"] = services
        return services


# --------------------------- команды бота --------------------------- #


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "Привет! Вас приветствует бот венчурного фонда Daily Challange для парсинга данных о русском венчуре. "
        "Используй команды внизу, чтобы пропарсить все каналы, какой-то конкретный канал, а также узнать "
        "информацию о людях.\n\n"
        "Команды:\n"
        "/parse — запустить парсинг каналов из config.json или переменных окружения\n"
        "/stats — показать статистику по найденным людям и проектам\n"
        "/people — список людей (инвесторы, ангелы, основатели, операторы, менторы)\n"
        "/projects — последние проекты\n"
        "/export — выгрузка в Excel\n"
        "/help — инструкция по использованию"
    )
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Как пользоваться ботом:\n"
        "1) Укажите токен и API-ключи Telegram (bot_config.json и config.json или переменные окружения).\n"
        "2) Добавьте нужные каналы в config.json (поле channels) или в переменную VC_CHANNELS.\n"
        "3) Запустите /parse — бот соберёт данные, определит роль человека "
        "(ментор/инвестор/бизнес-ангел/основатель/сотрудник) и сохранит в БД.\n"
        "4) Используйте /people, /projects и /export для просмотра результатов.\n\n"
        "Для Vercel используйте вебхук (см. инструкцию в ответе)."
    )
    await update.message.reply_text(text)


async def parse_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    services = await ensure_services(context.application)
    parser: AdvancedVCParser = services["parser"]
    classifier: VCClassifier = services["classifier"]
    database: VCDatabase = services["database"]
    parser_config = services["parser_config"]

    channels = parser_config.get("channels", [])
    if not channels:
        await update.message.reply_text("Нет каналов в config.json/VC_CHANNELS. Добавьте их и повторите.")
        return

    await update.message.reply_text("Запускаю парсинг, это займёт ~1-2 минуты...")

    all_results: List[Dict] = []
    people_count = 0
    projects_count = 0

    for channel in channels:
        try:
            results = await parser.parse_channel(channel, limit=parser_config.get("limit", 300))
            for item in results:
                enriched = classifier.enrich_data(item)
                all_results.append(enriched)
                if enriched.get("type") == "project":
                    database.add_project(enriched)
                    projects_count += 1
                else:
                    database.add_person(enriched)
                    people_count += 1
        except Exception as e:
            logger.error(f"Ошибка при парсинге {channel}: {e}")

    summary = (
        f"Парсинг завершён.\n"
        f"Каналов: {len(channels)}\n"
        f"Найдено записей: {len(all_results)}\n"
        f"Проекты: {projects_count}\n"
        f"Люди: {people_count}"
    )
    await update.message.reply_text(summary)

    if all_results:
        filename = f"vc_export_{update.effective_user.id}.xlsx"
        parser.save_to_excel(all_results, filename)
        with open(filename, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename="vc_data.xlsx",
                caption="Актуальная выгрузка по парсингу",
            )
        os.remove(filename)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    services = await ensure_services(context.application)
    database: VCDatabase = services["database"]
    data = database.get_statistics()

    message = (
        "Статистика по базе:\n"
        f"Люди: {data['total_people']}\n"
        f" - Инвесторы: {data['investors']}\n"
        f" - Бизнес-ангелы: {data['angels']}\n"
        f" - Менторы: {data['mentors']}\n"
        f" - Основатели: {data['founders']}\n"
        f" - Сотрудники: {data['operators']}\n"
        f"Проекты: {data['total_projects']} (перспективных: {data['promising_projects']})\n"
        f"Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    await update.message.reply_text(message)


async def show_people(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Инвесторы", callback_data="people_Инвестор"),
            InlineKeyboardButton("Бизнес-ангелы", callback_data="people_Бизнес-ангел"),
        ],
        [
            InlineKeyboardButton("Менторы", callback_data="people_Ментор"),
            InlineKeyboardButton("Основатели", callback_data="people_Основатель стартапа"),
        ],
        [
            InlineKeyboardButton("Сотрудники", callback_data="people_Работник стартапа"),
            InlineKeyboardButton("Все", callback_data="people_all"),
        ],
    ]
    await update.message.reply_text(
        "Выберите категорию людей:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    services = await ensure_services(context.application)
    database: VCDatabase = services["database"]
    projects = database.get_projects(limit=10)

    if not projects:
        await update.message.reply_text("Проектов пока нет. Запустите /parse.")
        return

    lines = ["Последние проекты:"]
    for idx, project in enumerate(projects[:10], start=1):
        name = project.get("project_name") or "Без названия"
        stage = project.get("investment_stage") or "N/A"
        theme = project.get("theme") or "N/A"
        lines.append(f"{idx}. {name} — стадия: {stage}, ниша: {theme}")
    await update.message.reply_text("\n".join(lines))


async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    services = await ensure_services(context.application)
    database: VCDatabase = services["database"]

    people = database.get_people(limit=1000)
    projects = database.get_projects(limit=1000)
    if not people and not projects:
        await update.message.reply_text("База пуста. Сначала запустите /parse.")
        return

    await update.message.reply_text("Готовлю Excel...")
    filename = f"vc_export_full_{update.effective_user.id}.xlsx"
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        if people:
            pd.DataFrame(people).to_excel(writer, sheet_name="Люди", index=False)
        if projects:
            pd.DataFrame(projects).to_excel(writer, sheet_name="Проекты", index=False)

    with open(filename, "rb") as f:
        await update.message.reply_document(
            document=f,
            filename="vc_export.xlsx",
            caption="Выгрузка базы",
        )
    os.remove(filename)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    services = await ensure_services(context.application)
    database: VCDatabase = services["database"]

    classification = None if query.data == "people_all" else query.data.replace("people_", "")
    people = database.get_people(classification=classification, limit=20)

    if not people:
        await query.edit_message_text("Нет данных для выбранной категории.")
        return

    lines = [f"Категория: {classification or 'Все'}"]
    for idx, person in enumerate(people[:10], start=1):
        name = person.get("person_name") or "Без имени"
        pos = person.get("position") or ""
        company = person.get("company") or ""
        role = person.get("classification") or ""
        lines.append(f"{idx}. {name} — {role}")
        if pos:
            lines.append(f"   Роль: {pos}")
        if company:
            lines.append(f"   Компания: {company}")
    await query.edit_message_text("\n".join(lines))


# --------------------------- фабрика приложения --------------------------- #


def register_handlers(application: Application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("parse", parse_channels))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("people", show_people))
    application.add_handler(CommandHandler("projects", show_projects))
    application.add_handler(CommandHandler("export", export_data))
    application.add_handler(CallbackQueryHandler(button_callback))


async def create_application(enable_scheduler: bool = True) -> Application:
    bot_token = load_bot_token()
    if not bot_token:
        raise RuntimeError("Не найден токен бота. Заполните bot_config.json или переменную BOT_TOKEN.")

    application = Application.builder().token(bot_token).build()
    application.bot_data["enable_scheduler"] = enable_scheduler

    # Предзагрузка сервисов при старте (используется тем же циклом событий)
    async def post_init(app: Application):
        await ensure_services(app)

    application.post_init = post_init
    register_handlers(application)
    return application


def main():
    """Запуск в режиме polling (локально)."""
    try:
        application = asyncio.run(create_application(enable_scheduler=True))
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Не удалось запустить бота: {e}")


if __name__ == "__main__":
    main()
