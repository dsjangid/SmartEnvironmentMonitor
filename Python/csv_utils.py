import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from database import DB_PATH, get_recent_readings

EXPORT_DIR = Path(__file__).resolve().parent.parent / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def export_history_to_csv(limit: int = 100) -> str:
    """Export recent sensor history to a CSV file and return the file path."""
    rows = get_recent_readings(limit=limit)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_path = EXPORT_DIR / f"environment_history_{timestamp}.csv"

    with file_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["timestamp", "temperature", "humidity"])
        for row in rows:
            writer.writerow([row["timestamp"], row["temperature"], row["humidity"]])

    return str(file_path)
