"""
Расширенный парсер Telegram-каналов для поиска данных по венчурному рынку.
Работает через Telethon и использует ключевые слова для выделения проектов
и людей, связанных с венчуром.
"""

import asyncio
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Message


def load_config() -> Optional[Dict]:
    """
    Загружает конфигурацию из переменных окружения (для Vercel)
    или из локального файла config.json.
    """
    env_api_id = os.getenv("TELEGRAM_API_ID")
    env_api_hash = os.getenv("TELEGRAM_API_HASH")
    env_phone = os.getenv("TELEGRAM_PHONE")
    env_channels = os.getenv("VC_CHANNELS")
    env_limit = os.getenv("VC_LIMIT")
    env_session = os.getenv("TELEGRAM_SESSION_STRING")

    if env_api_id and env_api_hash and env_phone:
        channels = []
        if env_channels:
            channels = [ch.strip() if ch.strip().startswith("@") else f"@{ch.strip()}"
                        for ch in env_channels.replace(";", ",").split(",") if ch.strip()]
        config = {
            "api_id": int(env_api_id),
            "api_hash": env_api_hash,
            "phone": env_phone,
            "channels": channels,
            "limit": int(env_limit or 300),
            "session_string": env_session,
        }
        return config

    try:
        with open("config.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if env_session:
                data["session_string"] = env_session
            return data
    except FileNotFoundError:
        print("Не найден config.json и не заданы переменные окружения TELEGRAM_API_ID/HASH/PHONE")
        return None


class AdvancedVCParser:
    """
    Парсер Telegram-каналов для данных о проектах и людях венчура.
    """

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        phone: str,
        session_string: Optional[str] = None,
        session_file: str = "vc_parser_session",
    ):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.session_string = session_string
        session = StringSession(session_string) if session_string else session_file
        self.client = TelegramClient(session, api_id, api_hash)

        # Ключевые слова для определения типов сообщений
        self.project_keywords = [
            "стартап", "startup", "раунд", "round", "seed", "pre-seed", "series a",
            "series b", "series c", "raise", "funding", "valuation", "оценка",
            "финансирование", "инвестиции", "привлек", "поднял", "закрыл раунд",
            "венчурный раунд", "раунд a", "раунд b", "раунд c",
        ]

        self.person_keyword_groups = {
            "investor": [
                "инвестор", "investor", "vc", "венчурный", "фонд", "fund",
                "gp", "lp", "венчурный партнер", "partner vc", "managing partner",
                "venture capital", "investment director", "директор по инвестициям",
            ],
            "angel": [
                "бизнес-ангел", "бизнес ангел", "angel investor", "business angel",
                "private investor", "частный инвестор", "ангельский инвестор",
            ],
            "mentor": [
                "ментор", "mentor", "advisor", "adviser", "трекер", "tracker",
                "эксперт", "coach", "консультант", "наставник",
            ],
            "founder": [
                "founder", "cofounder", "co-founder", "основатель", "сооснователь",
                "ceo", "cpo", "cto", "coo", "founding team",
            ],
            "operator": [
                "product manager", "продакт", "маркетолог", "growth", "bizdev",
                "sales", "developer", "engineer", "designer", "операционный директор",
                "руководитель направления", "lead", "head of", "team lead",
            ],
        }

    async def connect(self):
        """Устанавливает соединение с Telegram."""
        await self.client.start(phone=self.phone)
        print("Телеграм-клиент успешно запущен.")

    async def parse_channel(self, channel_username: str, limit: int = 500) -> List[Dict]:
        """Сканирует указанный канал и извлекает нужные сообщения."""
        results: List[Dict] = []
        try:
            print(f"Парсим канал: {channel_username}")
            messages = await self.client.get_messages(channel_username, limit=limit)
            print(f"Получено сообщений: {len(messages)}")

            for message in messages:
                if not message.text:
                    continue
                text_lower = message.text.lower()
                is_project = any(kw in text_lower for kw in self.project_keywords)
                person_hint = self._detect_person_hint(text_lower)

                if not is_project and not person_hint:
                    continue

                parsed = self.extract_extended_info(message, is_project, person_hint)
                if parsed:
                    results.append(parsed)

            print(f"Найдено релевантных записей: {len(results)}")
        except Exception as e:
            print(f"Ошибка парсинга канала {channel_username}: {e}")
        return results

    def extract_extended_info(
        self,
        message: Message,
        is_project: bool,
        person_hint: Optional[str],
    ) -> Optional[Dict]:
        """Формирует структуру данных по проекту или персоне."""
        text = message.text
        text_lower = text.lower()

        data: Dict[str, Optional[str]] = {
            "date": message.date.strftime("%Y-%m-%d %H:%M:%S") if message.date else None,
            "channel": getattr(message.chat, "title", "Unknown"),
            "message_id": message.id,
            "message_url": f"https://t.me/{getattr(message.chat, 'username', '')}/{message.id}"
            if getattr(message.chat, "username", None)
            else None,
        }

        if is_project:
            data["type"] = "project"
            data.update(self._extract_project_info(text, text_lower))
        else:
            data["type"] = "person"
            data.update(self._extract_person_info(text, text_lower, person_hint))

        data["contacts"] = self._extract_contacts(text)
        data["social_links"] = self._extract_social_links(text)
        data["links"] = self._extract_all_links(text)
        data["full_text"] = text[:2000] if len(text) > 2000 else text
        data["description"] = text[:500] if len(text) > 500 else text
        return data

    def _detect_person_hint(self, text_lower: str) -> Optional[str]:
        """Определяет базовую роль человека по ключевым словам."""
        scores = {}
        for role, keywords in self.person_keyword_groups.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[role] = score
        best_role = max(scores, key=scores.get)
        return best_role if scores[best_role] > 0 else None

    def _extract_project_info(self, text: str, text_lower: str) -> Dict:
        info: Dict[str, Optional[str]] = {}
        info["project_name"] = self._extract_project_name(text)
        info["investment_stage"] = self._extract_round_stage(text_lower)
        info["funding_amount"] = self._extract_funding_amount(text)
        info["theme"] = self._extract_theme(text_lower)
        info["founder"] = self._extract_founder(text)
        info["team"] = self._extract_team(text)
        info["project_investors"] = self._extract_investors(text)
        info["achievements"] = self._extract_achievements(text)
        return info

    def _extract_person_info(self, text: str, text_lower: str, person_hint: Optional[str]) -> Dict:
        info: Dict[str, Optional[str]] = {}
        info["person_name"] = self._extract_person_name(text)
        info["position"] = self._extract_position(text)
        info["company"] = self._extract_company(text)
        info["status"] = self._extract_status(text_lower)
        info["classification"] = person_hint or self._classify_person(text_lower)
        return info

    def _extract_project_name(self, text: str) -> Optional[str]:
        patterns = [
            r"проект[:\s]+([А-ЯA-Z][А-Яа-яA-Za-z0-9\s\-]{2,40})",
            r"стартап[:\s]+([А-ЯA-Z][А-Яа-яA-Za-z0-9\s\-]{2,40})",
            r"company[:\s]+([A-Z][A-Za-z0-9\s\-]{2,40})",
            r"([A-ZА-Я][A-Za-zА-Яа-я0-9\-\s]{3,40})\s+(поднял|привлек|закрыл раунд)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                return name[:60]
        return None

    def _extract_round_stage(self, text_lower: str) -> Optional[str]:
        stages = {
            "pre-seed": ["pre-seed", "pre seed", "пре-сид", "пресид", "preseed"],
            "seed": ["seed", "сид", "раунд seed"],
            "series a": ["series a", "раунд a", "серия a"],
            "series b": ["series b", "раунд b", "серия b"],
            "series c": ["series c", "раунд c", "серия c"],
            "angel": ["angel", "ангельский", "ангельский раунд"],
            "bridge": ["bridge", "мостовой", "bridge round"],
        }
        for stage, keywords in stages.items():
            if any(kw in text_lower for kw in keywords):
                return stage
        return None

    def _extract_funding_amount(self, text: str) -> Optional[str]:
        patterns = [
            r"(\$[\d\s.,]+[kmbKMB]?)",
            r"(\d[\d\s.,]+)\s*(млн|миллион|тыс|k|m|b|млрд)",
            r"([\d\s.,]+)\s*(₽|руб|рублей|доллар|usd|eur|евро)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None

    def _extract_theme(self, text_lower: str) -> Optional[str]:
        themes = {
            "FinTech": ["fintech", "финтех", "платеж", "оплата"],
            "EdTech": ["edtech", "образование", "ed tech"],
            "HealthTech": ["healthtech", "здоров", "health"],
            "AI/ML": ["ai", "искусственный интеллект", "machine learning", "ml"],
            "SaaS": ["saas", "b2b", "subscription"],
            "E-commerce": ["e-commerce", "маркетплейс", "commerce", "marketplace"],
        }
        for theme, keywords in themes.items():
            if any(kw in text_lower for kw in keywords):
                return theme
        return "other"

    def _extract_founder(self, text: str) -> Optional[str]:
        patterns = [
            r"(?:основател[ья]|founder|co-founder)[:\s]+([A-Za-zА-Яа-яёЁ][A-Za-zА-Яа-яёЁ\s\-]{3,60})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_team(self, text: str) -> Optional[str]:
        patterns = [
            r"команда[:\s]+([A-Za-zА-Яа-яёЁ,\s\-]{5,120})",
            r"team[:\s]+([A-Za-zА-Яа-яёЁ,\s\-]{5,120})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:200]
        return None

    def _extract_investors(self, text: str) -> Optional[str]:
        patterns = [
            r"инвестор[ы]?:\s+([A-Za-zА-Яа-яёЁ,\s\-]{3,120})",
            r"investor[s]?:\s+([A-Za-zА-Яа-яёЁ,\s\-]{3,120})",
            r"участн[ик|ики]\s+раунд[а]?:\s+([A-Za-zА-Яа-яёЁ,\s\-]{3,120})",
        ]
        investors: List[str] = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            investors.extend(matches)
        return ", ".join(investors[:5]) if investors else None

    def _extract_achievements(self, text: str) -> Optional[str]:
        keywords = ["достиг", "выручка", "mrr", "arr", "клиентов", "юзер", "рост"]
        if not any(kw in text.lower() for kw in keywords):
            return None
        sentences = re.split(r"[.!?]\s+", text)
        for sentence in sentences:
            if any(kw in sentence.lower() for kw in keywords):
                return sentence.strip()[:200]
        return None

    def _extract_person_name(self, text: str) -> Optional[str]:
        patterns = [
            r"([А-Я][а-яё]+\s+[А-Я][а-яё]+)",
            r"([A-Z][a-z]+\s+[A-Z][a-z]+)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0][:80]
        return None

    def _extract_position(self, text: str) -> Optional[str]:
        positions = [
            "ceo", "cpo", "cto", "coo", "founder", "co-founder", "partner",
            "investment director", "managing partner", "analyst", "associate",
            "principal", "venture partner", "product manager", "маркетолог",
            "руководитель", "директор", "менеджер", "growth", "bizdev", "sales",
        ]
        text_lower = text.lower()
        for pos in positions:
            if pos in text_lower:
                idx = text_lower.find(pos)
                start = max(0, idx - 25)
                end = min(len(text), idx + len(pos) + 25)
                context = text[start:end].strip()
                return context[:120]
        return None

    def _extract_company(self, text: str) -> Optional[str]:
        patterns = [
            r"в\s+([A-ZА-Я][A-Za-zА-Яа-я0-9\-\s]{2,40})",
            r"company[:\s]+([A-Z][A-Za-z0-9\-\s]{2,40})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()[:60]
        return None

    def _extract_status(self, text_lower: str) -> Optional[str]:
        if any(kw in text_lower for kw in ["основател", "founder", "соосновател"]):
            return "founder"
        if "стартап" in text_lower or "startup" in text_lower:
            return "startup"
        if "фонд" in text_lower or "fund" in text_lower:
            return "fund"
        return None

    def _classify_person(self, text_lower: str) -> str:
        role = self._detect_person_hint(text_lower)
        return role or "unknown"

    def _extract_contacts(self, text: str) -> Optional[str]:
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        phone_pattern = r"[\+]?[0-9]{10,15}"
        telegram_pattern = r"@[a-zA-Z0-9_]+|t\.me/[a-zA-Z0-9_]+"
        emails = re.findall(email_pattern, text)
        phones = re.findall(phone_pattern, text)
        telegrams = re.findall(telegram_pattern, text)
        contacts = emails + phones + telegrams
        return ", ".join(contacts[:5]) if contacts else None

    def _extract_social_links(self, text: str) -> Optional[str]:
        patterns = {
            "linkedin": r"linkedin\.com/[^\s]+",
            "twitter": r"(?:twitter|x)\.com/[^\s]+",
            "facebook": r"facebook\.com/[^\s]+",
            "instagram": r"instagram\.com/[^\s]+",
            "vk": r"vk\.com/[^\s]+",
            "telegram": r"t\.me/[^\s]+|telegram\.me/[^\s]+",
        }
        links: List[str] = []
        for platform, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            links.extend([f"{platform}:{m}" for m in matches[:2]])
        return ", ".join(links) if links else None

    def _extract_all_links(self, text: str) -> Optional[str]:
        url_pattern = r"https?://[^\s]+|www\.[^\s]+"
        links = re.findall(url_pattern, text)
        return ", ".join(links[:10]) if links else None

    async def parse_multiple_channels(self, channel_usernames: List[str], limit: int = 500) -> List[Dict]:
        """Парсит несколько каналов подряд."""
        all_results: List[Dict] = []
        for channel in channel_usernames:
            results = await self.parse_channel(channel, limit)
            all_results.extend(results)
            await asyncio.sleep(2)
        return all_results

    def save_to_excel(self, data: List[Dict], filename: str = "vc_data_advanced.xlsx"):
        if not data:
            print("Нет данных для сохранения.")
            return
        pd.DataFrame(data).to_excel(filename, index=False, engine="openpyxl")
        print(f"Файл сохранен: {filename}")

    def save_to_csv(self, data: List[Dict], filename: str = "vc_data_advanced.csv"):
        if not data:
            print("Нет данных для сохранения.")
            return
        pd.DataFrame(data).to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"Файл сохранен: {filename}")


async def main():
    print("=" * 60)
    print("TELEGRAM VC PARSER (расширенный)")
    print("=" * 60)

    config = load_config()
    if not config:
        return

    parser = AdvancedVCParser(
        api_id=config["api_id"],
        api_hash=config["api_hash"],
        phone=config["phone"],
        session_string=config.get("session_string"),
    )
    await parser.connect()

    channels = config.get("channels", [])
    if not channels:
        print("В config.json или переменных окружения не указаны каналы для парсинга.")
        return

    print(f"Старт парсинга {len(channels)} каналов...")
    results = await parser.parse_multiple_channels(channels, limit=config.get("limit", 300))

    if results:
        parser.save_to_excel(results, "vc_projects.xlsx")
        parser.save_to_csv(results, "vc_projects.csv")
        print(f"Собрано записей: {len(results)}")
    else:
        print("Релевантных сообщений не найдено.")

    await parser.client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

