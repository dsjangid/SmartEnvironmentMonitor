import os
import threading
from pathlib import Path

from flask import Flask, jsonify, send_file, send_from_directory

from csv_utils import export_history_to_csv
from receiver import EnvironmentSubscriber

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = PROJECT_ROOT / "Dashboard"

app = Flask(__name__, static_folder=str(DASHBOARD_DIR), static_url_path="")
subscriber = EnvironmentSubscriber()


@app.get("/")
def index() -> tuple[str, int]:
    return send_from_directory(DASHBOARD_DIR, "index.html"), 200


@app.get("/health")
def health() -> tuple[dict, int]:
    return jsonify({"status": "ok"}), 200


@app.get("/api/latest")
def latest_readings() -> tuple[dict, int]:
    readings = subscriber.get_latest_readings()
    has_data = readings.get("temperature") is not None and readings.get("humidity") is not None
    return jsonify({**readings, "status": "ok" if has_data else "waiting_for_sensor"}), 200


@app.get("/api/history")
def history_readings() -> tuple[dict, int]:
    return jsonify({"history": subscriber.get_history()}), 200


@app.get("/api/export/csv")
def export_csv() -> tuple[object, int]:
    file_path = export_history_to_csv(limit=100)
    return send_file(file_path, as_attachment=True, download_name="environment_history.csv"), 200


def start_mqtt_listener() -> None:
    subscriber.start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    mqtt_thread = threading.Thread(target=start_mqtt_listener, daemon=True)
    mqtt_thread.start()
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
