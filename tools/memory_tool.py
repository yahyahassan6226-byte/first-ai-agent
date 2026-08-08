import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "memory.db"


def init_db():
    """Abuur table-ka memory haddii uusan jirin."""
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def save_memory(key: str, value: str) -> str:
    """Kaydi ama update-garee memory."""
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO memories (key, value)
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
        """,
        (key, value),
    )

    conn.commit()
    conn.close()

    return f"Memory saved: {key} = {value}"


def get_memory(key: str) -> str:
    """Soo celi memory key gaar ah."""
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT value FROM memories WHERE key = ?",
        (key,),
    )

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return f"No memory found for key: {key}"

    return row[0]


def list_memories() -> str:
    """Soo celi dhammaan memories-ka."""
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT key, value FROM memories ORDER BY key"
    )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "No memories saved."

    return "\n".join(
        f"{key}: {value}"
        for key, value in rows
    )