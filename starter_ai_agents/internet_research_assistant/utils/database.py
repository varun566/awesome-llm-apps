import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta as _timedelta
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id  TEXT UNIQUE NOT NULL,
    session_id  TEXT NOT NULL,
    role        TEXT NOT NULL,
    content     TEXT NOT NULL,
    metadata    TEXT DEFAULT '{}',
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);

CREATE TABLE IF NOT EXISTS search_cache (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key   TEXT UNIQUE NOT NULL,
    cache_value TEXT NOT NULL,
    hits        INTEGER DEFAULT 0,
    expires_at  TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_search_cache_key ON search_cache(cache_key);

CREATE TABLE IF NOT EXISTS search_analytics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL,
    query       TEXT NOT NULL,
    sources     INTEGER DEFAULT 0,
    cached      INTEGER DEFAULT 0,
    duration_ms INTEGER DEFAULT 0,
    created_at  TEXT NOT NULL
);
"""


class Database:
    def __init__(self, db_path: str = "research_assistant.db"):
        self.db_path = db_path
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
        return self._local.conn

    @contextmanager
    def _cursor(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

    def _init_db(self) -> None:
        with self._cursor() as cur:
            cur.executescript(_SCHEMA)
        logger.info(f"Database initialised at {self.db_path}")

    # ------------------------------------------------------------------ #
    #  Conversations                                                       #
    # ------------------------------------------------------------------ #

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> str:
        message_id = str(uuid.uuid4())
        with self._cursor() as cur:
            cur.execute(
                """INSERT INTO conversations
                   (message_id, session_id, role, content, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    message_id,
                    session_id,
                    role,
                    content,
                    json.dumps(metadata or {}),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
        return message_id

    def get_conversation(self, session_id: str, limit: int = 50) -> list:
        with self._cursor() as cur:
            cur.execute(
                """SELECT * FROM conversations
                   WHERE session_id = ?
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (session_id, limit),
            )
            rows = cur.fetchall()
        return [dict(r) for r in reversed(rows)]

    def list_sessions(self, limit: int = 20) -> list:
        with self._cursor() as cur:
            cur.execute(
                """SELECT session_id,
                          MIN(created_at) as started_at,
                          MAX(created_at) as last_active,
                          COUNT(*) as message_count
                   FROM conversations
                   GROUP BY session_id
                   ORDER BY last_active DESC
                   LIMIT ?""",
                (limit,),
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def delete_session(self, session_id: str) -> None:
        with self._cursor() as cur:
            cur.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))

    # ------------------------------------------------------------------ #
    #  Persistent cache                                                   #
    # ------------------------------------------------------------------ #

    def cache_get(self, key: str) -> Optional[str]:
        now = datetime.now(timezone.utc).isoformat()
        with self._cursor() as cur:
            cur.execute(
                "SELECT cache_value FROM search_cache WHERE cache_key = ? AND expires_at > ?",
                (key, now),
            )
            row = cur.fetchone()
            if row:
                cur.execute(
                    "UPDATE search_cache SET hits = hits + 1 WHERE cache_key = ?",
                    (key,),
                )
                return row["cache_value"]
        return None

    def cache_set(self, key: str, value: str, ttl_seconds: int = 3600) -> None:
        """Store a value in the persistent search cache with a TTL.

        Args:
            key: Cache key (typically a SHA-256 hash of the query).
            value: Serialised value to store.
            ttl_seconds: Time-to-live in seconds (default 1 hour).
                         An existing entry for the same key is overwritten.
        """

        expires_at = (datetime.now(timezone.utc) + _timedelta(seconds=ttl_seconds)).isoformat()
        with self._cursor() as cur:
            cur.execute(
                """INSERT INTO search_cache (cache_key, cache_value, expires_at, created_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(cache_key) DO UPDATE SET
                       cache_value = excluded.cache_value,
                       expires_at  = excluded.expires_at,
                       hits        = 0""",
                (key, value, expires_at, datetime.now(timezone.utc).isoformat()),
            )

    def cache_purge_expired(self) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._cursor() as cur:
            cur.execute("DELETE FROM search_cache WHERE expires_at <= ?", (now,))
            return cur.rowcount

    # ------------------------------------------------------------------ #
    #  Analytics                                                          #
    # ------------------------------------------------------------------ #

    def log_search(
        self,
        session_id: str,
        query: str,
        sources: int = 0,
        cached: bool = False,
        duration_ms: int = 0,
    ) -> None:
        with self._cursor() as cur:
            cur.execute(
                """INSERT INTO search_analytics
                   (session_id, query, sources, cached, duration_ms, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    query,
                    sources,
                    int(cached),
                    duration_ms,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    def get_analytics(self, limit: int = 100) -> list:
        with self._cursor() as cur:
            cur.execute(
                "SELECT * FROM search_analytics ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
