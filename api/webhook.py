"""
ASGI-обработчик для Vercel. Принимает вебхуки от Telegram и прокидывает их
в наше приложение python-telegram-bot.
"""

import asyncio
import os

from fastapi import FastAPI, Header, HTTPException, Request
from telegram import Update

from advanced_bot import create_application, ensure_services

app = FastAPI()

WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
bot_application = None
bot_lock = asyncio.Lock()


async def get_bot_application():
    global bot_application
    if bot_application:
        return bot_application

    async with bot_lock:
        if bot_application:
            return bot_application
        bot_application = await create_application(enable_scheduler=False)
        await bot_application.initialize()
        await bot_application.start()
        await ensure_services(bot_application)
        return bot_application


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None),
):
    if WEBHOOK_SECRET and x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Bad secret token")

    payload = await request.json()
    application = await get_bot_application()
    update = Update.de_json(payload, application.bot)
    await application.process_update(update)
    return {"ok": True}
