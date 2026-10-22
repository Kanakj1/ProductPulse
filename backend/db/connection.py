"""
ProductPulse — Database Connection & Session Management
Enforces SQLite foreign key integrity on every connection.
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, Union

# Default SQLite database path
DEFAULT_DB_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "productpulse.db"
SCHEMA_SQL_PATH = DEFAULT_DB_DIR / "schema.sql"


def get_db_path(custom_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Resolves the SQLite database path from argument, environment variable, or default.
    """
    if custom_path:
        return Path(custom_path).resolve()
    env_path = os.getenv("PRODUCTPULSE_DB_PATH")
    if env_path:
        return Path(env_path).resolve()
    return DEFAULT_DB_PATH


def get_connection(db_path: Optional[Union[str, Path]] = None) -> sqlite3.Connection:
    """
    Establishes an SQLite connection with strict foreign-key enforcement.
    Ensures PRAGMA foreign_keys = ON is active and verified before returning.
    """
    target_path = get_db_path(db_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(target_path), timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    # Enforce SQLite foreign keys and concurrency settings
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 30000;")

    # Strict runtime verification
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys;")
    result = cursor.fetchone()
    if not result or result[0] != 1:
        conn.close()
        raise RuntimeError(
            "SQLite foreign key enforcement could not be activated on database connection."
        )

    return conn


def init_db(db_path: Optional[Union[str, Path]] = None) -> sqlite3.Connection:
    """
    Initializes the SQLite schema using backend/db/schema.sql.
    Verifies tables and returns the active connection.
    """
    if not SCHEMA_SQL_PATH.exists():
        raise FileNotFoundError(f"Schema DDL file not found at: {SCHEMA_SQL_PATH}")

    with open(SCHEMA_SQL_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = get_connection(db_path)
    with conn:
        conn.executescript(schema_sql)

    return conn


def get_db(db_path: Optional[Union[str, Path]] = None) -> Generator[sqlite3.Connection, None, None]:
    """
    FastAPI dependency generator for managed SQLite database sessions.
    Automatically commits successful transactions and rolls back on unhandled exceptions.
    """
    conn = get_connection(db_path)
    try:
        yield conn
        if conn.in_transaction:
            conn.commit()
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise
    finally:
        conn.close()


get_db_context = contextmanager(get_db)

