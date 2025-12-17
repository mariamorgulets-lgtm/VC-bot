"""
Простой тест для проверки работы бота
"""

import json
import logging
import asyncio
from telegram import Bot

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def test_bot_async():
    """Тестирует подключение к боту (асинхронная версия)"""
    try:
        # Загружаем конфигурацию
        with open('bot_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        bot_token = config.get('bot_token')
        if not bot_token:
            print("❌ Ошибка: не указан bot_token в bot_config.json")
            return False
        
        print(f"🔍 Проверяю подключение к боту...")
        print(f"📝 Токен: {bot_token[:10]}...{bot_token[-10:]}")
        
        # Создаем бота
        bot = Bot(token=bot_token)
        
        # Получаем информацию о боте (асинхронно)
        bot_info = await bot.get_me()
        
        print(f"\n✅ Бот подключен успешно!")
        print(f"📋 Имя бота: {bot_info.first_name}")
        print(f"👤 Username: @{bot_info.username}")
        print(f"🆔 ID бота: {bot_info.id}")
        
        return True
        
    except FileNotFoundError:
        print("❌ Ошибка: файл bot_config.json не найден")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка в формате bot_config.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка при подключении к боту: {e}")
        print("\nВозможные причины:")
        print("1. Неправильный токен бота")
        print("2. Проблемы с интернет-соединением")
        print("3. Бот был удален или заблокирован")
        return False

def test_bot():
    """Обертка для запуска асинхронной функции"""
    try:
        return asyncio.run(test_bot_async())
    except Exception as e:
        print(f"❌ Ошибка при запуске теста: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("ТЕСТ ПОДКЛЮЧЕНИЯ К TELEGRAM БОТУ")
    print("=" * 60)
    print()
    
    if test_bot():
        print("\n✅ Тест пройден! Бот должен работать.")
        print("\nТеперь запустите telegram_bot.py и попробуйте отправить /start")
    else:
        print("\n❌ Тест не пройден. Исправьте ошибки и попробуйте снова.")

