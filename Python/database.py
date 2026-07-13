import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "environment.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_reading(temperature: float, humidity: float) -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO readings (timestamp, temperature, humidity) VALUES (?, ?, ?)",
        (datetime.now(timezone.utc).isoformat(), temperature, humidity),
    )
    conn.commit()
    conn.close()


def get_recent_readings(limit: int = 20) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT timestamp, temperature, humidity FROM readings ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()

    result = []
    for timestamp, temperature, humidity in reversed(rows):
        result.append(
            {
                "timestamp": timestamp,
                "temperature": temperature,
                "humidity": humidity,
            }
        )
    return result
