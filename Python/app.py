import os
import time
import threading
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory

from csv_utils import export_history_to_csv
from database import get_system_metrics
from receiver import EnvironmentSubscriber

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = PROJECT_ROOT / "Dashboard"

app = Flask(__name__, static_folder=str(DASHBOARD_DIR), static_url_path="")
subscriber = EnvironmentSubscriber()
START_TIME = time.time()


@app.get("/")
def index() -> tuple[str, int]:
    return send_from_directory(DASHBOARD_DIR, "index.html"), 200


@app.get("/health")
def health() -> tuple[dict, int]:
    uptime = round(time.time() - START_TIME, 2)
    return jsonify({
        "status": "ok",
        "uptime_seconds": uptime,
        "service": "SmartEnvironmentMonitor API",
    }), 200


@app.get("/api/latest")
def latest_readings() -> tuple[dict, int]:
    readings = subscriber.get_latest_readings()
    has_data = readings.get("temperature") is not None and readings.get("humidity") is not None
    return jsonify({**readings, "status": "ok" if has_data else "waiting_for_sensor"}), 200


@app.get("/api/history")
def history_readings() -> tuple[dict, int]:
    limit_param = request.args.get("limit", default="30")
    try:
        limit = max(1, min(int(limit_param), 500))
    except ValueError:
        limit = 30
    return jsonify({"history": subscriber.get_history(limit=limit)}), 200


@app.get("/api/metrics")
def metrics() -> tuple[dict, int]:
    metrics_data = get_system_metrics()
    uptime = round(time.time() - START_TIME, 2)
    return jsonify({
        "status": "ok",
        "uptime_seconds": uptime,
        "database_metrics": metrics_data,
    }), 200


@app.get("/api/export/csv")
def export_csv() -> tuple[object, int]:
    limit_param = request.args.get("limit", default="100")
    try:
        limit = max(1, min(int(limit_param), 1000))
    except ValueError:
        limit = 100

    file_path = export_history_to_csv(limit=limit)
    return send_file(file_path, as_attachment=True, download_name="environment_history.csv"), 200


def start_mqtt_listener() -> None:
    subscriber.start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    mqtt_thread = threading.Thread(target=start_mqtt_listener, daemon=True)
    mqtt_thread.start()
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
