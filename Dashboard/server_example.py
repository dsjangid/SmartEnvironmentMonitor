"""
Minimal Flask backend for testing the dashboard without ESP32/MQTT.

Run:
    python3 -m pip install flask
    python3 server_example.py

Then open Dashboard/index.html through a local static server and set
CONFIG.API_BASE_URL to "http://localhost:5000" if needed.
"""

import csv
import random
import tempfile
import threading
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, send_file

app = Flask(__name__)

history = []
latest_reading = {
    "temperature": None,
    "humidity": None,
    "timestamp": None,
    "status": "waiting_for_sensor",
}


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def _simulate_mqtt_updates() -> None:
    """Stand-in for ESP32 -> MQTT -> Python subscriber updates."""
    while True:
        reading = {
            "temperature": round(24 + random.uniform(-3, 6), 1),
            "humidity": round(48 + random.uniform(-8, 8), 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "ok",
        }
        latest_reading.update(reading)
        history.append(reading.copy())
        del history[:-60]
        time.sleep(4)


@app.get("/api/latest")
def get_latest():
    return jsonify(latest_reading)


@app.get("/api/history")
def get_history():
    return jsonify({"history": history})


@app.get("/api/export/csv")
def export_csv():
    temp_file = tempfile.NamedTemporaryFile("w", newline="", suffix=".csv", delete=False)
    with temp_file:
        writer = csv.writer(temp_file)
        writer.writerow(["timestamp", "temperature", "humidity"])
        for row in history:
            writer.writerow([row["timestamp"], row["temperature"], row["humidity"]])

    return send_file(temp_file.name, as_attachment=True, download_name="environment_history.csv")


if __name__ == "__main__":
    threading.Thread(target=_simulate_mqtt_updates, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=True)
