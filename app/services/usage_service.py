import sqlite3
from datetime import date, timedelta
from pathlib import Path
from threading import Lock

from app.config import BASE_DIR, FREE_DAILY_LIMIT

DB_PATH = Path(BASE_DIR) / "usage.db"


class UsageService:
    """Controla cuántas descargas gratuitas usó cada usuario hoy y quién
    tiene el plan PRO activo (descargas ilimitadas).

    user_key es un identificador de texto genérico: puede ser un usuario
    de Telegram ("tg:123456789") o un visitante anónimo del sitio web
    identificado por cookie de sesión ("web:<uuid>"). Así el mismo motor
    de límites/PRO sirve para ambos canales.
    """

    def __init__(self, db_path=DB_PATH, daily_limit=FREE_DAILY_LIMIT):
        self.db_path = db_path
        self.daily_limit = daily_limit
        self._lock = Lock()
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS usage (
                    user_key TEXT NOT NULL,
                    usage_date TEXT NOT NULL,
                    count INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (user_key, usage_date)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pro_users (
                    user_key TEXT PRIMARY KEY,
                    pro_until TEXT
                )
                """
            )
            self._migrate_legacy_schema(conn)

    def _migrate_legacy_schema(self, conn):
        """Si existe una usage.db de una versión anterior (columna
        telegram_id en vez de user_key), la migra sola en vez de romper."""
        for table in ("usage", "pro_users"):
            cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]

            if "user_key" in cols:
                continue

            if "telegram_id" in cols:
                try:
                    conn.execute(f"ALTER TABLE {table} RENAME COLUMN telegram_id TO user_key")
                except sqlite3.OperationalError:
                    # SQLite muy viejo, sin soporte de RENAME COLUMN: recreamos vacía.
                    conn.execute(f"DROP TABLE {table}")
                    self._init_db()

    @staticmethod
    def _today():
        return date.today().isoformat()

    def is_pro(self, user_key):
        user_key = str(user_key)
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT pro_until FROM pro_users WHERE user_key = ?",
                (user_key,),
            ).fetchone()

        if not row or not row[0]:
            return False

        return date.fromisoformat(row[0]) >= date.today()

    def pro_until(self, user_key):
        user_key = str(user_key)
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT pro_until FROM pro_users WHERE user_key = ?",
                (user_key,),
            ).fetchone()
        return row[0] if row else None

    def usage_today(self, user_key):
        user_key = str(user_key)
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT count FROM usage WHERE user_key = ? AND usage_date = ?",
                (user_key, self._today()),
            ).fetchone()
        return row[0] if row else 0

    def remaining_today(self, user_key):
        """None significa ilimitado (usuario PRO)."""
        if self.is_pro(user_key):
            return None
        return max(0, self.daily_limit - self.usage_today(user_key))

    def can_download(self, user_key):
        if self.is_pro(user_key):
            return True
        return self.usage_today(user_key) < self.daily_limit

    def register_download(self, user_key):
        user_key = str(user_key)
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO usage (user_key, usage_date, count)
                VALUES (?, ?, 1)
                ON CONFLICT(user_key, usage_date)
                DO UPDATE SET count = count + 1
                """,
                (user_key, self._today()),
            )

    def set_pro(self, user_key, days=30):
        user_key = str(user_key)
        until = (date.today() + timedelta(days=days)).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO pro_users (user_key, pro_until)
                VALUES (?, ?)
                ON CONFLICT(user_key)
                DO UPDATE SET pro_until = excluded.pro_until
                """,
                (user_key, until),
            )
        return until
