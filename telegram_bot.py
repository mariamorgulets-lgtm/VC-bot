"""
Telegram бот для парсинга венчурных каналов
Доступен другим пользователям через Telegram
"""

import asyncio
import json
import logging
from typing import List, Dict
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram_parser import TelegramVCParser, load_config
import os

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальные переменные
parser_instance = None
bot_config = None
parser_config = None  # Конфигурация парсера (с каналами)

def load_bot_config():
    """Загружает конфигурацию бота"""
    try:
        with open('bot_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Файл bot_config.json не найден!")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    try:
        logger.info(f"Получена команда /start от пользователя {update.effective_user.id}")
        welcome_message = """
🤖 <b>Бот для поиска венчурных проектов и инвесторов</b>

Я помогаю находить информацию о стартапах и инвесторах в Telegram каналах.

<b>Доступные команды:</b>
/start - Показать это сообщение
/parse - Парсить каналы из конфигурации
/parse_channel <канал> - Парсить конкретный канал
/help - Справка по использованию
/stats - Статистика последнего парсинга

<b>Примеры:</b>
/parse_channel @rusven
/parse_channel @ventureStuff

Начните с команды /parse для парсинга всех каналов из списка!
        """
        await update.message.reply_text(welcome_message, parse_mode='HTML')
        logger.info(f"Отправлено приветственное сообщение пользователю {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Ошибка при обработке /start: {e}")
        try:
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
        except:
            pass

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📖 <b>Справка по использованию бота</b>

<b>1. Парсинг всех каналов:</b>
/parse
Парсит все каналы, указанные в конфигурации

<b>2. Парсинг одного канала:</b>
/parse_channel @имя_канала
Например: /parse_channel @rusven

<b>3. Статистика:</b>
/stats
Показывает результаты последнего парсинга

<b>Важно:</b>
• Убедитесь, что вы подписаны на каналы, которые хотите парсить
• Для приватных каналов нужна подписка
• Парсинг может занять некоторое время

<b>Результаты:</b>
После парсинга бот отправит вам файл Excel с найденными проектами и инвесторами.
    """
    await update.message.reply_text(help_text, parse_mode='HTML')

async def parse_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Парсит все каналы из конфигурации"""
    global parser_instance, parser_config
    
    if not parser_instance:
        await update.message.reply_text("❌ Бот не инициализирован. Проверьте конфигурацию.")
        return
    
    if not parser_config:
        await update.message.reply_text("❌ Конфигурация парсера не загружена.")
        return
    
    await update.message.reply_text("🔍 Начинаю парсинг каналов... Это может занять несколько минут.")
    
    try:
        channels = parser_config.get('channels', [])
        if not channels:
            await update.message.reply_text("❌ В конфигурации не указаны каналы для парсинга.")
            return
        
        # Парсим каналы
        results = await parser_instance.parse_multiple_channels(
            channels, 
            limit=parser_config.get('limit', 100)
        )
        
        if not results:
            await update.message.reply_text("⚠️ Не найдено релевантных сообщений в указанных каналах.")
            return
        
        # Сохраняем результаты
        filename = f'vc_projects_{update.message.chat_id}.xlsx'
        parser_instance.save_to_excel(results, filename)
        
        # Отправляем статистику
        projects = [r for r in results if r['type'] == 'Проект']
        investors = [r for r in results if r['type'] == 'Инвестор']
        
        stats_message = f"""
✅ <b>Парсинг завершен!</b>

📊 <b>Статистика:</b>
• Всего найдено записей: {len(results)}
• Проектов: {len(projects)}
• Инвесторов: {len(investors)}
• Каналов обработано: {len(channels)}

📁 Файл с результатами готовится к отправке...
        """
        await update.message.reply_text(stats_message, parse_mode='HTML')
        
        # Отправляем файл
        with open(filename, 'rb') as file:
            await update.message.reply_document(
                document=file,
                filename='vc_projects.xlsx',
                caption='📊 Результаты парсинга венчурных каналов'
            )
        
        # Удаляем временный файл
        if os.path.exists(filename):
            os.remove(filename)
            
    except Exception as e:
        logger.error(f"Ошибка при парсинге: {e}")
        await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}")

async def parse_single_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Парсит один указанный канал"""
    global parser_instance, parser_config
    
    if not parser_instance:
        await update.message.reply_text("❌ Бот не инициализирован. Проверьте конфигурацию.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Укажите канал для парсинга.\nПример: /parse_channel @rusven")
        return
    
    channel = context.args[0]
    # Убираем @ если есть
    if channel.startswith('@'):
        channel = channel[1:]
    channel = '@' + channel
    
    await update.message.reply_text(f"🔍 Парсинг канала {channel}...")
    
    try:
        limit = parser_config.get('limit', 100) if parser_config else 100
        results = await parser_instance.parse_channel(channel, limit=limit)
        
        if not results:
            await update.message.reply_text(f"⚠️ В канале {channel} не найдено релевантных сообщений.")
            return
        
        # Сохраняем результаты
        filename = f'vc_projects_{update.message.chat_id}_{channel.replace("@", "")}.xlsx'
        parser_instance.save_to_excel(results, filename)
        
        # Статистика
        projects = [r for r in results if r['type'] == 'Проект']
        investors = [r for r in results if r['type'] == 'Инвестор']
        
        stats_message = f"""
✅ <b>Парсинг завершен!</b>

📊 <b>Статистика по каналу {channel}:</b>
• Всего найдено: {len(results)}
• Проектов: {len(projects)}
• Инвесторов: {len(investors)}

📁 Файл готовится...
        """
        await update.message.reply_text(stats_message, parse_mode='HTML')
        
        # Отправляем файл
        with open(filename, 'rb') as file:
            await update.message.reply_document(
                document=file,
                filename=f'vc_projects_{channel.replace("@", "")}.xlsx',
                caption=f'📊 Результаты парсинга канала {channel}'
            )
        
        # Удаляем временный файл
        if os.path.exists(filename):
            os.remove(filename)
            
    except Exception as e:
        logger.error(f"Ошибка при парсинге канала {channel}: {e}")
        await update.message.reply_text(f"❌ Ошибка при парсинге: {str(e)}\n\nПроверьте:\n• Правильность имени канала\n• Подписку на канал (если он приватный)")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику"""
    global parser_config
    
    stats_text = """
📊 <b>Статистика бота</b>

Используйте команду /parse или /parse_channel для получения актуальной статистики.

<b>Доступные каналы в конфигурации:</b>
"""
    if parser_config and 'channels' in parser_config:
        channels_list = '\n'.join([f"• {ch}" for ch in parser_config['channels']])
        stats_text += channels_list
    else:
        stats_text += "Каналы не настроены"
    
    await update.message.reply_text(stats_text, parse_mode='HTML')

async def init_parser():
    """Инициализирует парсер"""
    global parser_instance, parser_config
    
    # Загружаем конфигурацию парсера
    parser_config = load_config()
    if not parser_config:
        logger.error("Не удалось загрузить конфигурацию парсера")
        return False
    
    # Создаем экземпляр парсера
    parser_instance = TelegramVCParser(
        api_id=parser_config['api_id'],
        api_hash=parser_config['api_hash'],
        phone=parser_config['phone']
    )
    
    # Подключаемся к Telegram
    try:
        await parser_instance.connect()
        logger.info("Парсер успешно инициализирован")
        return True
    except Exception as e:
        logger.error(f"Ошибка при инициализации парсера: {e}")
        return False

def main():
    """Основная функция запуска бота"""
    # Загружаем конфигурацию бота
    config = load_bot_config()
    if not config:
        print("❌ Ошибка: не найден файл bot_config.json")
        print("Создайте файл bot_config.json с токеном бота")
        return
    
    bot_token = config.get('bot_token')
    if not bot_token:
        print("❌ Ошибка: не указан bot_token в bot_config.json")
        return
    
    # Создаем приложение бота
    application = Application.builder().token(bot_token).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("parse", parse_channels))
    application.add_handler(CommandHandler("parse_channel", parse_single_channel))
    application.add_handler(CommandHandler("stats", stats))
    
    # Инициализируем парсер при запуске (в фоне, не блокируя бота)
    async def post_init(app: Application):
        try:
            logger.info("Начинаю инициализацию парсера...")
            result = await init_parser()
            if result:
                logger.info("✅ Парсер успешно инициализирован")
            else:
                logger.warning("⚠️ Парсер не инициализирован, но бот будет работать")
        except Exception as e:
            logger.error(f"Ошибка при инициализации парсера: {e}")
            logger.info("Бот будет работать, но парсинг может быть недоступен")
    
    application.post_init = post_init
    
    # Добавляем обработчик ошибок
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Ошибка при обработке обновления: {context.error}")
        if isinstance(update, Update) and update.message:
            try:
                await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
            except:
                pass
    
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    print("🤖 Бот запущен! Нажмите Ctrl+C для остановки.")
    print("📝 Проверьте логи выше на наличие ошибок")
    logger.info("Запуск бота...")
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    main()
