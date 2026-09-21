import sqlite3
from collections.abc import Generator
from backend.app.config import settings

def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Create a new SQLite connection with foreign keys enabled and row_factory configured."""
    target_path = db_path or settings.DATABASE_PATH
    conn = sqlite3.connect(target_path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def get_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency for obtaining a database connection safely."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
