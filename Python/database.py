import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "environment.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def init_db(db_path: Path = DB_PATH) -> None:
    """Initialize SQLite database table and index for high-performance querying."""
    conn = sqlite3.connect(db_path)
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
    # Index on timestamp for fast date range filtering
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON readings(timestamp)"
    )
    conn.commit()
    conn.close()


def save_reading(temperature: float, humidity: float, db_path: Path = DB_PATH) -> None:
    """Persist a single sensor reading pair to SQLite."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO readings (timestamp, temperature, humidity) VALUES (?, ?, ?)",
        (datetime.now(timezone.utc).isoformat(), temperature, humidity),
    )
    conn.commit()
    conn.close()


def get_recent_readings(limit: int = 20, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve recent readings ordered chronologically."""
    conn = sqlite3.connect(db_path)
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
                "temperature": round(temperature, 1),
                "humidity": round(humidity, 1),
            }
        )
    return result


def get_system_metrics(db_path: Path = DB_PATH) -> Dict[str, Any]:
    """Calculate system-wide analytics, statistical metrics, and storage footprint."""
    if not db_path.exists():
        return {
            "total_readings": 0,
            "min_temperature": None,
            "max_temperature": None,
            "avg_temperature": None,
            "min_humidity": None,
            "max_humidity": None,
            "avg_humidity": None,
            "db_size_kb": 0.0,
        }

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 
            COUNT(*), 
            MIN(temperature), MAX(temperature), AVG(temperature),
            MIN(humidity), MAX(humidity), AVG(humidity)
        FROM readings
        """
    )
    count, min_t, max_t, avg_t, min_h, max_h, avg_h = cursor.fetchone()
    conn.close()

    db_size = round(db_path.stat().st_size / 1024.0, 2) if db_path.exists() else 0.0

    return {
        "total_readings": count or 0,
        "min_temperature": round(min_t, 1) if min_t is not None else None,
        "max_temperature": round(max_t, 1) if max_t is not None else None,
        "avg_temperature": round(avg_t, 1) if avg_t is not None else None,
        "min_humidity": round(min_h, 1) if min_h is not None else None,
        "max_humidity": round(max_h, 1) if max_h is not None else None,
        "avg_humidity": round(avg_h, 1) if avg_h is not None else None,
        "db_size_kb": db_size,
    }
