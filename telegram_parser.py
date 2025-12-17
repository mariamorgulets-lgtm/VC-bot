"""
Парсер Telegram каналов для поиска венчурных проектов и инвесторов
Использует библиотеку Telethon для работы с Telegram API
"""

import asyncio
import re
import json
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
from telethon import TelegramClient
from telethon.tl.types import Message
import os

# Загрузка конфигурации
def load_config():
    """Загружает конфигурацию из файла config.json"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ Файл config.json не найден!")
        print("Создайте файл config.json с вашими API ключами")
        return None

class TelegramVCParser:
    """Класс для парсинга венчурных каналов в Telegram"""
    
    def __init__(self, api_id: int, api_hash: str, phone: str):
        """
        Инициализация клиента Telegram
        
        Args:
            api_id: API ID из my.telegram.org
            api_hash: API Hash из my.telegram.org
            phone: Номер телефона в формате +7XXXXXXXXXX
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.client = TelegramClient('vc_parser_session', api_id, api_hash)
        
        # Ключевые слова для поиска проектов
        self.project_keywords = [
            'стартап', 'startup', 'проект', 'раунд', 'round', 'инвестиции',
            'funding', 'seed', 'series a', 'series b', 'pre-seed', 'ангел',
            'angel', 'венчур', 'venture', 'vc', 'инвестор', 'investor',
            'привлечение', 'raise', 'valuation', 'оценка', 'unicorn'
        ]
        
        # Ключевые слова для поиска инвесторов
        self.investor_keywords = [
            'инвестор', 'investor', 'фонд', 'fund', 'vc', 'венчурный',
            'venture capital', 'angel', 'ангел', 'акселератор', 'accelerator',
            'инвестирует', 'invests', 'portfolio', 'портфель'
        ]
    
    async def connect(self):
        """Подключение к Telegram"""
        await self.client.start(phone=self.phone)
        print("✅ Успешно подключено к Telegram!")
    
    async def parse_channel(self, channel_username: str, limit: int = 100) -> List[Dict]:
        """
        Парсит сообщения из канала
        
        Args:
            channel_username: Имя канала (например, 'vc_channel' или полная ссылка)
            limit: Максимальное количество сообщений для парсинга
        
        Returns:
            Список словарей с информацией о найденных проектах/инвесторах
        """
        results = []
        
        try:
            print(f"🔍 Парсинг канала: {channel_username}")
            
            # Получаем сообщения из канала
            messages = await self.client.get_messages(channel_username, limit=limit)
            
            print(f"📨 Найдено {len(messages)} сообщений")
            
            for message in messages:
                if not message.text:
                    continue
                
                text = message.text.lower()
                
                # Проверяем, содержит ли сообщение информацию о проекте
                is_project = any(keyword in text for keyword in self.project_keywords)
                is_investor = any(keyword in text for keyword in self.investor_keywords)
                
                if is_project or is_investor:
                    parsed_data = self.extract_info(message, is_project, is_investor)
                    if parsed_data:
                        results.append(parsed_data)
            
            print(f"✅ Найдено {len(results)} релевантных сообщений")
            
        except Exception as e:
            print(f"❌ Ошибка при парсинге канала {channel_username}: {e}")
        
        return results
    
    def extract_info(self, message: Message, is_project: bool, is_investor: bool) -> Optional[Dict]:
        """
        Извлекает информацию из сообщения
        
        Args:
            message: Объект сообщения Telegram
            is_project: Флаг, что это проект
            is_investor: Флаг, что это инвестор
        
        Returns:
            Словарь с извлеченной информацией
        """
        text = message.text
        
        # Извлечение названия проекта/компании
        project_name = self.extract_project_name(text)
        
        # Извлечение суммы инвестиций
        funding_amount = self.extract_funding_amount(text)
        
        # Извлечение стадии раунда
        round_stage = self.extract_round_stage(text)
        
        # Извлечение инвесторов
        investors = self.extract_investors(text)
        
        # Извлечение ссылок
        links = self.extract_links(text)
        
        # Извлечение контактов
        contacts = self.extract_contacts(text)
        
        # Извлечение описания
        description = text[:500] if len(text) > 500 else text
        
        return {
            'date': message.date.strftime('%Y-%m-%d %H:%M:%S') if message.date else None,
            'channel': message.chat.title if hasattr(message.chat, 'title') else 'Unknown',
            'message_id': message.id,
            'type': 'Проект' if is_project else ('Инвестор' if is_investor else 'Другое'),
            'project_name': project_name,
            'funding_amount': funding_amount,
            'round_stage': round_stage,
            'investors': investors,
            'links': links,
            'contacts': contacts,
            'description': description,
            'full_text': text
        }
    
    def extract_project_name(self, text: str) -> Optional[str]:
        """Извлекает название проекта из текста"""
        # Паттерны для поиска названий
        patterns = [
            r'стартап[:\s]+([А-ЯЁA-Z][А-ЯЁа-яёA-Za-z\s]+)',
            r'проект[:\s]+([А-ЯЁA-Z][А-ЯЁа-яёA-Za-z\s]+)',
            r'компания[:\s]+([А-ЯЁA-Z][А-ЯЁа-яёA-Za-z\s]+)',
            r'([А-ЯЁA-Z][А-ЯЁа-яёA-Za-z\s]{3,20})\s+(привлек|привлекает|раунд)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_funding_amount(self, text: str) -> Optional[str]:
        """Извлекает сумму инвестиций"""
        # Паттерны для сумм в разных валютах
        patterns = [
            r'(\$[\d,\.]+[KMB]?)\s*(доллар|usd|dollar)',
            r'(\d+[\s,\.]?\d*[\s,\.]?\d*)\s*(млн|миллион|million|млрд|миллиард|billion)',
            r'(\$[\d,\.]+[KMB]?)',
            r'(\d+[\s,\.]?\d*[\s,\.]?\d*)\s*(рубл|rub|₽)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        
        return None
    
    def extract_round_stage(self, text: str) -> Optional[str]:
        """Извлекает стадию раунда"""
        stages = {
            'pre-seed': ['pre-seed', 'пре-сид', 'пресид'],
            'seed': ['seed', 'сид', 'посевной'],
            'series a': ['series a', 'серия а', 'раунд а'],
            'series b': ['series b', 'серия б', 'раунд б'],
            'series c': ['series c', 'серия с', 'раунд с'],
            'angel': ['angel', 'ангел', 'ангельский'],
        }
        
        text_lower = text.lower()
        for stage, keywords in stages.items():
            if any(keyword in text_lower for keyword in keywords):
                return stage
        
        return None
    
    def extract_investors(self, text: str) -> Optional[str]:
        """Извлекает имена инвесторов"""
        patterns = [
            r'инвестор[ы]?[:\s]+([А-ЯЁA-Z][А-ЯЁа-яёA-Za-z\s,]+)',
            r'фонд[ы]?[:\s]+([А-ЯЁA-Z][А-ЯЁа-яёA-Za-z\s,]+)',
            r'при участии[:\s]+([А-ЯЁA-Z][А-ЯЁа-яёA-Za-z\s,]+)',
        ]
        
        investors = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            investors.extend(matches)
        
        return ', '.join(investors) if investors else None
    
    def extract_links(self, text: str) -> Optional[str]:
        """Извлекает ссылки из текста"""
        url_pattern = r'https?://[^\s]+|www\.[^\s]+|t\.me/[^\s]+'
        links = re.findall(url_pattern, text)
        return ', '.join(links) if links else None
    
    def extract_contacts(self, text: str) -> Optional[str]:
        """Извлекает контакты (email, telegram)"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        telegram_pattern = r'@[a-zA-Z0-9_]+|t\.me/[a-zA-Z0-9_]+'
        
        emails = re.findall(email_pattern, text)
        telegrams = re.findall(telegram_pattern, text)
        
        contacts = emails + telegrams
        return ', '.join(contacts) if contacts else None
    
    async def parse_multiple_channels(self, channel_usernames: List[str], limit: int = 100) -> List[Dict]:
        """Парсит несколько каналов"""
        all_results = []
        
        for channel in channel_usernames:
            results = await self.parse_channel(channel, limit)
            all_results.extend(results)
            await asyncio.sleep(2)  # Пауза между каналами
        
        return all_results
    
    def save_to_excel(self, data: List[Dict], filename: str = 'vc_projects.xlsx'):
        """Сохраняет данные в Excel файл"""
        if not data:
            print("⚠️ Нет данных для сохранения")
            return
        
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"✅ Данные сохранены в {filename}")
    
    def save_to_csv(self, data: List[Dict], filename: str = 'vc_projects.csv'):
        """Сохраняет данные в CSV файл"""
        if not data:
            print("⚠️ Нет данных для сохранения")
            return
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ Данные сохранены в {filename}")


async def main():
    """Основная функция для запуска парсера"""
    print("=" * 60)
    print("ПАРСЕР TELEGRAM КАНАЛОВ ДЛЯ ВЕНЧУРНЫХ ПРОЕКТОВ")
    print("=" * 60)
    
    # Загрузка конфигурации
    config = load_config()
    if not config:
        return
    
    # Инициализация парсера
    parser = TelegramVCParser(
        api_id=config['api_id'],
        api_hash=config['api_hash'],
        phone=config['phone']
    )
    
    # Подключение
    await parser.connect()
    
    # Список каналов для парсинга (укажите свои каналы)
    channels = config.get('channels', [])
    
    if not channels:
        print("\n⚠️ В config.json не указаны каналы для парсинга")
        print("Добавьте список каналов в поле 'channels'")
        print("\nПример использования:")
        print("  channels = ['@vc_channel1', '@vc_channel2']")
        return
    
    # Парсинг каналов
    print(f"\n📋 Начинаю парсинг {len(channels)} каналов...")
    results = await parser.parse_multiple_channels(channels, limit=config.get('limit', 100))
    
    # Сохранение результатов
    if results:
        parser.save_to_excel(results, 'vc_projects.xlsx')
        parser.save_to_csv(results, 'vc_projects.csv')
        
        print(f"\n📊 Статистика:")
        print(f"  Всего найдено записей: {len(results)}")
        projects = [r for r in results if r['type'] == 'Проект']
        investors = [r for r in results if r['type'] == 'Инвестор']
        print(f"  Проектов: {len(projects)}")
        print(f"  Инвесторов: {len(investors)}")
    else:
        print("\n⚠️ Не найдено релевантных сообщений")
    
    await parser.client.disconnect()
    print("\n✅ Парсинг завершен!")


if __name__ == '__main__':
    asyncio.run(main())



