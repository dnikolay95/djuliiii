import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiosqlite

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime(ISO_FORMAT)


class Database:
    def __init__(self, conn: aiosqlite.Connection, db_path: str) -> None:
        self._conn = conn
        self.db_path = db_path

    @classmethod
    async def create(cls, db_path: str) -> "Database":
        if db_path:
            os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        conn = await aiosqlite.connect(db_path)
        conn.row_factory = aiosqlite.Row
        db = cls(conn, db_path)
        await db._init_schema()
        return db

    async def close(self) -> None:
        await self._conn.close()

    async def _init_schema(self) -> None:
        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_user_id INTEGER NOT NULL UNIQUE,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS greetings_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_user_id INTEGER NOT NULL,
                greeting_text TEXT NOT NULL,
                sent_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_greetings_user ON greetings_log (tg_user_id);

            CREATE TABLE IF NOT EXISTS messages_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_user_id INTEGER NOT NULL,
                message_text TEXT,
                message_type TEXT NOT NULL,
                raw_payload TEXT,
                received_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_messages_user ON messages_log (tg_user_id);
            CREATE INDEX IF NOT EXISTS idx_messages_type ON messages_log (message_type);
            """
        )
        await self._conn.commit()

    async def upsert_user(
        self,
        tg_user_id: int,
        first_name: Optional[str],
        last_name: Optional[str],
        username: Optional[str],
        seen_at: Optional[str] = None,
    ) -> None:
        seen = seen_at or utc_now()
        await self._conn.execute(
            """
            INSERT INTO users (
                tg_user_id, first_name, last_name, username, first_seen_at, last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(tg_user_id) DO UPDATE SET
                first_name=excluded.first_name,
                last_name=excluded.last_name,
                username=excluded.username,
                last_seen_at=excluded.last_seen_at,
                first_seen_at=COALESCE(users.first_seen_at, excluded.first_seen_at)
            """,
            (tg_user_id, first_name, last_name, username, seen, seen),
        )
        await self._conn.commit()

    async def add_greeting(
        self, tg_user_id: int, greeting_text: str, sent_at: Optional[str] = None
    ) -> None:
        ts = sent_at or utc_now()
        await self._conn.execute(
            """
            INSERT INTO greetings_log (tg_user_id, greeting_text, sent_at)
            VALUES (?, ?, ?)
            """,
            (tg_user_id, greeting_text, ts),
        )
        await self._conn.commit()

    async def add_message(
        self,
        tg_user_id: int,
        message_text: Optional[str],
        message_type: str,
        raw_payload: Optional[str] = None,
        received_at: Optional[str] = None,
    ) -> None:
        ts = received_at or utc_now()
        await self._conn.execute(
            """
            INSERT INTO messages_log (tg_user_id, message_text, message_type, raw_payload, received_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (tg_user_id, message_text, message_type, raw_payload, ts),
        )
        await self._conn.commit()

    async def list_users(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        cursor = await self._conn.execute(
            """
            SELECT
                u.*,
                IFNULL(g.count, 0) AS greetings_count
            FROM users u
            LEFT JOIN (
                SELECT tg_user_id, COUNT(*) AS count
                FROM greetings_log
                GROUP BY tg_user_id
            ) g ON g.tg_user_id = u.tg_user_id
            ORDER BY u.last_seen_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_user(self, tg_user_id: int) -> Optional[Dict[str, Any]]:
        cursor = await self._conn.execute(
            """
            SELECT
                u.*,
                IFNULL(g.count, 0) AS greetings_count
            FROM users u
            LEFT JOIN (
                SELECT tg_user_id, COUNT(*) AS count
                FROM greetings_log
                GROUP BY tg_user_id
            ) g ON g.tg_user_id = u.tg_user_id
            WHERE u.tg_user_id = ?
            """,
            (tg_user_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def list_greetings(
        self, limit: int = 50, offset: int = 0, tg_user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT tg_user_id, greeting_text, sent_at
            FROM greetings_log
        """
        params: List[Any] = []
        if tg_user_id is not None:
            query += " WHERE tg_user_id = ?"
            params.append(tg_user_id)
        query += " ORDER BY sent_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor = await self._conn.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def list_messages(
        self,
        limit: int = 50,
        offset: int = 0,
        tg_user_id: Optional[int] = None,
        message_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT tg_user_id, message_text, message_type, raw_payload, received_at
            FROM messages_log
        """
        clauses = []
        params: List[Any] = []
        if tg_user_id is not None:
            clauses.append("tg_user_id = ?")
            params.append(tg_user_id)
        if message_type is not None:
            clauses.append("message_type = ?")
            params.append(message_type)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY received_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor = await self._conn.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_stats(self) -> Dict[str, Any]:
        cursor = await self._conn.execute("SELECT COUNT(*) AS total_users FROM users")
        total_users = (await cursor.fetchone())["total_users"]

        cursor = await self._conn.execute(
            "SELECT COUNT(*) AS total_greetings FROM greetings_log"
        )
        total_greetings = (await cursor.fetchone())["total_greetings"]

        cursor = await self._conn.execute(
            "SELECT COUNT(*) AS total_messages FROM messages_log"
        )
        total_messages = (await cursor.fetchone())["total_messages"]

        cursor = await self._conn.execute(
            """
            SELECT tg_user_id, COUNT(*) AS greetings_count
            FROM greetings_log
            GROUP BY tg_user_id
            ORDER BY greetings_count DESC
            LIMIT 10
            """
        )
        top_users = [dict(row) for row in await cursor.fetchall()]

        return {
            "total_users": total_users,
            "total_greetings": total_greetings,
            "total_messages": total_messages,
            "top_users": top_users,
        }


