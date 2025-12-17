"""
Планировщик периодического парсинга каналов (по умолчанию раз в 3 дня).
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from advanced_parser import AdvancedVCParser, load_config
from classifier import VCClassifier
from database import VCDatabase

logger = logging.getLogger(__name__)


class ParsingScheduler:
    def __init__(self, parser: AdvancedVCParser, classifier: VCClassifier, database: VCDatabase, enabled: bool = True):
        self.parser = parser
        self.classifier = classifier
        self.database = database
        self.enabled = enabled
        self.is_running = False
        self.last_parse_date: Optional[datetime] = None
        self.parse_interval_days = 3

    async def start(self):
        if not self.enabled:
            logger.info("Планировщик отключен (режим Vercel или ручной запуск).")
            return
        self.is_running = True
        logger.info("Планировщик парсинга запущен.")
        asyncio.create_task(self._scheduler_loop())

    async def _scheduler_loop(self):
        while self.is_running:
            try:
                if self._should_parse():
                    logger.info("Запускаем плановый парсинг каналов...")
                    await self.run_parsing()
                    self.last_parse_date = datetime.now()
                await asyncio.sleep(3600)  # проверяем раз в час
            except Exception as e:
                logger.error(f"Сбой в планировщике: {e}")
                await asyncio.sleep(3600)

    def _should_parse(self) -> bool:
        if self.last_parse_date is None:
            return True
        return (datetime.now() - self.last_parse_date) >= timedelta(days=self.parse_interval_days)

    async def run_parsing(self):
        try:
            config = load_config()
            if not config:
                logger.error("Не удалось загрузить конфигурацию парсера.")
                return

            channels = config.get("channels", [])
            if not channels:
                logger.warning("Нет каналов для парсинга.")
                return

            all_results = []
            for channel in channels:
                try:
                    results = await self.parser.parse_channel(channel, limit=config.get("limit", 300))
                    enriched_results = []
                    people_count = 0
                    projects_count = 0

                    for result in results:
                        enriched = self.classifier.enrich_data(result)
                        enriched_results.append(enriched)
                        if enriched.get("type") == "project":
                            self.database.add_project(enriched)
                            projects_count += 1
                        else:
                            self.database.add_person(enriched)
                            people_count += 1

                    self.database.add_parsing_history(channel, len(results), people_count, projects_count)
                    all_results.extend(enriched_results)
                    logger.info(f"{channel}: обработано {len(results)} сообщений.")
                except Exception as e:
                    logger.error(f"Сбой при парсинге канала {channel}: {e}")

            logger.info(f"Плановый парсинг завершен. Всего новых записей: {len(all_results)}")
        except Exception as e:
            logger.error(f"Ошибка планировщика: {e}")

    def stop(self):
        self.is_running = False
        logger.info("Планировщик остановлен.")

