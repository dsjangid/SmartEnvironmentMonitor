# Smart Environment Monitoring System

A professional IoT project that monitors temperature and humidity using an ESP32, publishes sensor data over MQTT, processes it in Python, and visualizes it through a Flask-powered dashboard.

## Project Overview

This project demonstrates a complete end-to-end Internet of Things pipeline:

1. ESP32 reads environmental data from a DHT22 sensor.
2. The ESP32 connects to Wi-Fi and publishes readings to an MQTT broker.
3. A Python subscriber receives the data from MQTT.
4. A Flask backend exposes the latest readings through a REST API.
5. A web dashboard displays live telemetry and trends.

## Architecture

```text
DHT22 Sensor
    │
    ▼
ESP32 (Wokwi / real board)
    │
    ▼
Wi-Fi
    │
    ▼
MQTT Broker (HiveMQ)
    │
    ▼
Python MQTT Subscriber
    │
    ▼
Flask Backend API
    │
    ▼
Dashboard UI
```

## Features

- Live temperature monitoring
- Live humidity monitoring
- MQTT-based data communication
- Flask REST API
- Modern dashboard UI
- Responsive web design
- SQLite history storage
- CSV export
- Alert thresholds for out-of-range readings
- Professional project structure for GitHub and internships

## Folder Structure

```text
SmartEnvironmentMonitor/
├── ESP32/
│   ├── sketch.ino
│   ├── diagram.json
│   ├── libraries.txt
│   └── wokwi-project.txt
├── Python/
│   ├── receiver.py
│   ├── app.py
│   ├── database.py
│   ├── csv_utils.py
│   └── requirements.txt
├── Dashboard/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── config.js
├── data/               # created automatically for SQLite database
├── exports/            # created automatically for CSV exports
└── README.md
```

## Hardware and Software Used

### Hardware
- ESP32
- DHT22 sensor
- Wi-Fi network

### Software
- Arduino / PlatformIO-style sketch development
- MQTT protocol
- Python
- Flask
- HTML, CSS, JavaScript
- Chart.js
- Wokwi simulator

## Prerequisites

Before running the project, install:

- Python 3.9+
- Flask
- paho-mqtt

You can install the Python dependencies with:

```bash
python3 -m pip install -r Python/requirements.txt
```

## Running the Project

### 1. Upload the ESP32 code

Open the ESP32 sketch in the ESP32 folder and upload it to your ESP32 board or run it in Wokwi.

Make sure the Wi-Fi credentials and MQTT broker settings are correct.

### 2. Start the Python backend

From the project root:

```bash
python3 Python/app.py
```

This starts:
- the Flask web server
- the MQTT subscriber
- SQLite history storage

### 3. Open the dashboard

Open your browser and visit:

```text
http://127.0.0.1:5000/
```

## API Endpoints

### Health check

```text
GET /health
```

### Latest sensor readings

```text
GET /api/latest
```

Example response:

```json
{
  "temperature": 28.4,
  "humidity": 62.1,
  "timestamp": "2026-07-13T10:30:00+00:00",
  "status": "ok"
}
```

### Recent history

```text
GET /api/history
```

### CSV export

```text
GET /api/export/csv
```

## Learning Goals Covered

This project helps you understand:

- Embedded systems
- ESP32 programming
- GPIO and sensor communication
- Wi-Fi networking
- MQTT publish/subscribe
- Python callbacks and event-driven programming
- Flask and REST APIs
- Web dashboards and Chart.js
- End-to-end IoT architecture

## Future Improvements

Possible next steps for the project:

- Add alert rules and notifications
- Add authentication and security improvements
- Deploy to cloud services

## License

This project is licensed under the MIT License.
