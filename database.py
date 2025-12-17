"""
Простая обертка над SQLite для хранения проектов и людей.
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional


class VCDatabase:
    def __init__(self, db_path: str = "vc_database.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_name TEXT,
                position TEXT,
                company TEXT,
                status TEXT,
                classification TEXT,
                classification_confidence REAL,
                secondary_roles TEXT,
                contacts TEXT,
                social_links TEXT,
                description TEXT,
                full_text TEXT,
                channel TEXT,
                message_id INTEGER,
                message_url TEXT,
                date_found TEXT,
                date_added TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT,
                investment_stage TEXT,
                funding_amount TEXT,
                theme TEXT,
                founder TEXT,
                team TEXT,
                project_investors TEXT,
                achievements TEXT,
                relevance_score REAL,
                is_promising INTEGER,
                recommendation TEXT,
                links TEXT,
                contacts TEXT,
                description TEXT,
                full_text TEXT,
                channel TEXT,
                message_id INTEGER,
                message_url TEXT,
                date_found TEXT,
                date_added TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS parsing_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT,
                messages_parsed INTEGER,
                people_found INTEGER,
                projects_found INTEGER,
                date_parsed TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_people_classification ON people(classification)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_people_date ON people(date_added)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_stage ON projects(investment_stage)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_date ON projects(date_added)")

        # Миграции для старых баз: добавляем недостающие столбцы, если их нет
        self._ensure_column(cursor, "people", "secondary_roles", "TEXT")
        self._ensure_column(cursor, "people", "classification_confidence", "REAL")

        conn.commit()
        conn.close()

    def _ensure_column(self, cursor: sqlite3.Cursor, table: str, column: str, col_type: str):
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [row[1] for row in cursor.fetchall()]
        if column not in cols:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

    def add_person(self, data: Dict) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if data.get("message_id"):
            cursor.execute(
                """SELECT id FROM people WHERE message_id = ? AND channel = ?""",
                (data["message_id"], data.get("channel", "")),
            )
            existing = cursor.fetchone()
            if existing:
                conn.close()
                return existing[0]

        cursor.execute(
            """
            INSERT INTO people (
                person_name, position, company, status, classification,
                classification_confidence, secondary_roles, contacts, social_links,
                description, full_text, channel, message_id, message_url, date_found
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data.get("person_name"),
                data.get("position"),
                data.get("company"),
                data.get("status"),
                data.get("person_classification", data.get("classification")),
                data.get("classification_confidence", 0.0),
                data.get("secondary_roles"),
                data.get("contacts"),
                data.get("social_links"),
                data.get("description"),
                data.get("full_text"),
                data.get("channel"),
                data.get("message_id"),
                data.get("message_url"),
                data.get("date"),
            ),
        )

        person_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return person_id

    def add_project(self, data: Dict) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if data.get("message_id"):
            cursor.execute(
                """SELECT id FROM projects WHERE message_id = ? AND channel = ?""",
                (data["message_id"], data.get("channel", "")),
            )
            existing = cursor.fetchone()
            if existing:
                conn.close()
                return existing[0]

        cursor.execute(
            """
            INSERT INTO projects (
                project_name, investment_stage, funding_amount, theme,
                founder, team, project_investors, achievements,
                relevance_score, is_promising, recommendation,
                links, contacts, description, full_text,
                channel, message_id, message_url, date_found
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data.get("project_name"),
                data.get("investment_stage"),
                data.get("funding_amount"),
                data.get("theme"),
                data.get("founder"),
                data.get("team"),
                data.get("project_investors"),
                data.get("achievements"),
                data.get("project_relevance", 0.0),
                int(data.get("is_promising", False)),
                data.get("recommendation"),
                data.get("links"),
                data.get("contacts"),
                data.get("description"),
                data.get("full_text"),
                data.get("channel"),
                data.get("message_id"),
                data.get("message_url"),
                data.get("date"),
            ),
        )

        project_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return project_id

    def get_people(self, classification: Optional[str] = None, limit: int = 100) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if classification:
            cursor.execute(
                """
                SELECT * FROM people
                WHERE classification = ? AND is_active = 1
                ORDER BY date_added DESC
                LIMIT ?
            """,
                (classification, limit),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM people
                WHERE is_active = 1
                ORDER BY date_added DESC
                LIMIT ?
            """,
                (limit,),
            )

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_projects(self, stage: Optional[str] = None, limit: int = 100) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if stage:
            cursor.execute(
                """
                SELECT * FROM projects
                WHERE investment_stage = ? AND is_active = 1
                ORDER BY date_added DESC
                LIMIT ?
            """,
                (stage, limit),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM projects
                WHERE is_active = 1
                ORDER BY date_added DESC
                LIMIT ?
            """,
                (limit,),
            )

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_statistics(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM people WHERE is_active = 1')
        total_people = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM people WHERE classification = "Ментор" AND is_active = 1')
        mentors = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM people WHERE classification = "Инвестор" AND is_active = 1')
        investors = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM people WHERE classification = "Бизнес-ангел" AND is_active = 1')
        angels = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM people WHERE classification = "Основатель стартапа" AND is_active = 1')
        founders = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM people WHERE classification = "Работник стартапа" AND is_active = 1')
        operators = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM projects WHERE is_active = 1')
        total_projects = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM projects WHERE is_promising = 1 AND is_active = 1')
        promising_projects = cursor.fetchone()[0]

        conn.close()
        return {
            "total_people": total_people,
            "mentors": mentors,
            "investors": investors,
            "angels": angels,
            "founders": founders,
            "operators": operators,
            "total_projects": total_projects,
            "promising_projects": promising_projects,
        }

    def add_parsing_history(self, channel: str, messages_parsed: int, people_found: int, projects_found: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO parsing_history (channel, messages_parsed, people_found, projects_found)
            VALUES (?, ?, ?, ?)
        """,
            (channel, messages_parsed, people_found, projects_found),
        )
        conn.commit()
        conn.close()
