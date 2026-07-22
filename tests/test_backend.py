import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add Python directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "Python"))

from database import init_db, save_reading, get_recent_readings, get_system_metrics
from csv_utils import export_history_to_csv, EXPORT_DIR
from app import app


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        temp_db_path = Path(tf.name)
    
    init_db(db_path=temp_db_path)
    yield temp_db_path

    if temp_db_path.exists():
        temp_db_path.unlink()


@pytest.fixture
def client():
    """Flask test client fixture."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_database_init_and_insertion(temp_db):
    """Test SQLite database initialization, reading insertion, and retrieval."""
    save_reading(24.5, 55.2, db_path=temp_db)
    save_reading(25.1, 56.0, db_path=temp_db)

    readings = get_recent_readings(limit=10, db_path=temp_db)
    assert len(readings) == 2
    assert readings[0]["temperature"] == 24.5
    assert readings[0]["humidity"] == 55.2
    assert readings[1]["temperature"] == 25.1
    assert readings[1]["humidity"] == 56.0


def test_database_system_metrics(temp_db):
    """Test computation of min, max, avg, and total readings in metrics."""
    metrics_empty = get_system_metrics(db_path=temp_db)
    assert metrics_empty["total_readings"] == 0

    save_reading(20.0, 40.0, db_path=temp_db)
    save_reading(30.0, 60.0, db_path=temp_db)

    metrics = get_system_metrics(db_path=temp_db)
    assert metrics["total_readings"] == 2
    assert metrics["min_temperature"] == 20.0
    assert metrics["max_temperature"] == 30.0
    assert metrics["avg_temperature"] == 25.0
    assert metrics["min_humidity"] == 40.0
    assert metrics["max_humidity"] == 60.0
    assert metrics["avg_humidity"] == 50.0
    assert metrics["db_size_kb"] > 0


def test_flask_health_endpoint(client):
    """Test GET /health API endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert "uptime_seconds" in data


def test_flask_latest_endpoint(client):
    """Test GET /api/latest API endpoint."""
    response = client.get("/api/latest")
    assert response.status_code == 200
    data = response.get_json()
    assert "status" in data
    assert "temperature" in data
    assert "humidity" in data


def test_flask_history_endpoint(client):
    """Test GET /api/history API endpoint."""
    response = client.get("/api/history?limit=5")
    assert response.status_code == 200
    data = response.get_json()
    assert "history" in data
    assert isinstance(data["history"], list)


def test_flask_metrics_endpoint(client):
    """Test GET /api/metrics API endpoint."""
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert "database_metrics" in data


def test_flask_csv_export_endpoint(client):
    """Test GET /api/export/csv API endpoint."""
    response = client.get("/api/export/csv")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
