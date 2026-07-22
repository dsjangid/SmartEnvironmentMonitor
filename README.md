# Smart Environment Monitoring System

An end-to-end IoT environment monitor that reads temperature and humidity from a DHT22 sensor on an ESP32, publishes the readings over MQTT, stores them with a Python backend, and displays live telemetry in a browser dashboard.

## Preview

### Dashboard

<img src="Images/dashboard%20top.png" alt="Dashboard top section" width="100%">

<img src="Images/dashboard%20bottom.png" alt="Dashboard history and export section" width="100%">

### Wokwi Simulation

<img src="Images/Wokwi.png" alt="Wokwi ESP32 simulation" width="100%">

<img src="Images/wokwi%20and%20terminal.png" alt="Wokwi simulation with terminal output" width="100%">

### CSV Export

<img src="Images/csv%20history%20.png" alt="CSV history export" width="100%">

## What This Project Does

The project is split into three working parts:

- `ESP32/` contains the Arduino sketch for an ESP32 connected to a DHT22 sensor.
- `Python/` contains the Flask API, MQTT subscriber, SQLite storage, and CSV export utilities.
- `Dashboard/` contains the browser UI for live readings, trend charts, history, alerts, and CSV download.

The default setup uses the public HiveMQ broker at `broker.hivemq.com` and these MQTT topics:

- `divyansh/environment/temperature`
- `divyansh/environment/humidity`

## Architecture

```text
DHT22 Sensor
    |
    v
ESP32
    |
    | Wi-Fi
    v
HiveMQ MQTT Broker
    |
    v
Python MQTT Subscriber
    |
    v
SQLite Database + Flask API
    |
    v
Dashboard UI
```

## Features

- ESP32 + DHT22 temperature and humidity sensing
- MQTT publish/subscribe communication
- Python subscriber for live sensor ingestion
- Flask API for dashboard and data access
- SQLite storage in `data/environment.db`
- Recent history endpoint for trend charts and tables
- CSV export saved under `exports/`
- Responsive dashboard with Chart.js charts and sparklines
- Connection status, waiting state, offline notice, and alert banner
- Configurable dashboard polling interval and alert thresholds
- Wokwi simulator files for testing without physical hardware

## Folder Structure

```text
SmartEnvironmentMonitor/
├── ESP32/
│   ├── sketch.ino            # ESP32 firmware
│   ├── diagram.json          # Wokwi circuit diagram
│   ├── libraries.txt         # Wokwi/Arduino libraries
│   └── wokwi-project.txt
├── Python/
│   ├── app.py                # Flask app + MQTT listener startup
│   ├── receiver.py           # MQTT subscriber logic
│   ├── database.py           # SQLite setup and queries
│   ├── csv_utils.py          # CSV export helper
│   └── requirements.txt
├── Dashboard/
│   ├── index.html            # Dashboard markup
│   ├── style.css             # Dashboard styling
│   ├── app.js                # Polling, charts, alerts, export
│   ├── config.js             # API endpoints, thresholds, intervals
│   ├── server_example.py     # Optional standalone test backend
│   └── README.md
├── data/
│   └── environment.db        # Created/used by the backend
├── exports/                  # Timestamped CSV exports
└── README.md
```

## Requirements

### Hardware

- ESP32 board or Wokwi ESP32 simulation
- DHT22 temperature and humidity sensor
- Wi-Fi connection

### Software

- Python 3.9+
- Arduino IDE, PlatformIO, or Wokwi
- Python packages from `Python/requirements.txt`

Python dependencies:

```bash
python3 -m pip install -r Python/requirements.txt
```

## ESP32 Setup

Open [ESP32/sketch.ino](</Users/meydivyansh/Projects /SmartEnvironmentMonitor/ESP32/sketch.ino>) in Arduino IDE, PlatformIO, or Wokwi.

Default firmware settings:

```cpp
const char* ssid = "Wokwi-GUEST";
const char* password = "";
const char* mqtt_server = "broker.hivemq.com";
const int DHT_PIN = 15;
const int PUBLISH_INTERVAL_MS = 2000;
```

For a real ESP32 board, update `ssid` and `password` with your Wi-Fi credentials. The sketch publishes temperature and humidity every 2 seconds as plain numeric values.

Required Arduino/Wokwi libraries:

- `DHT sensor library for ESPx`
- `PubSubClient`

## Running The Backend

From the project root:

```bash
python3 Python/app.py
```

This starts:

- the Flask web server on `http://127.0.0.1:5000`
- the MQTT subscriber in a background thread
- SQLite database initialization
- the dashboard static file server

You can change the Flask port with the `PORT` environment variable:

```bash
PORT=8000 python3 Python/app.py
```

## Opening The Dashboard

After starting the backend, open:

```text
http://127.0.0.1:5000/
```

The dashboard polls `/api/latest` every 5 seconds and `/api/history` every 10 seconds. These values can be changed in [Dashboard/config.js](</Users/meydivyansh/Projects /SmartEnvironmentMonitor/Dashboard/config.js>).

Dashboard thresholds are also configured in `Dashboard/config.js`:

```js
temperature: { min: 10, max: 35, unit: "°C" }
humidity: { min: 20, max: 70, unit: "%RH" }
```

## API Endpoints

### Health Check

```text
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

### Latest Reading

```text
GET /api/latest
```

Response when data is available:

```json
{
  "temperature": 28.4,
  "humidity": 62.1,
  "timestamp": "2026-07-13T10:30:00+00:00",
  "status": "ok"
}
```

Before the first MQTT readings arrive, `temperature` and `humidity` are `null` and the status is `waiting_for_sensor`.

### Recent History

```text
GET /api/history
```

Returns the latest stored readings from SQLite:

```json
{
  "history": [
    {
      "timestamp": "2026-07-13T10:30:00+00:00",
      "temperature": 28.4,
      "humidity": 62.1
    }
  ]
}
```

### CSV Export

```text
GET /api/export/csv
```

Exports up to 100 recent readings as `environment_history.csv` to the browser and also creates a timestamped CSV file in `exports/`.

## Data Storage

The backend stores paired temperature and humidity readings in SQLite. A row is saved only after both the temperature topic and humidity topic have received fresh values.

Database file:

```text
data/environment.db
```

CSV export files:

```text
exports/environment_history_YYYYMMDD_HHMMSS.csv
```

## Performance Metrics

These metrics are based on the current default configuration:

- ESP32 publish interval: `2000 ms` (`ESP32/sketch.ino`)
- Dashboard poll interval: `5000 ms` (`Dashboard/config.js`)

### 1) Power Consumption (ESP32 @ 3.3V)

- **Wi-Fi active mode (typical ESP32 range):** ~`80–260 mA` → **`264–858 mW`**
- **Deep sleep mode (typical ESP32 range):** ~`10–150 µA` → **`0.033–0.495 mW`**

> Note: this firmware does not currently enter deep sleep; values above are hardware reference ranges and can vary by board, regulator, and radio conditions.

### 2) MQTT Latency (Sensor Read → Dashboard)

- Sensor values are produced every **2 seconds**.
- MQTT transport + backend processing are typically sub-second on stable networks.
- Dashboard refresh is polling-based every **5 seconds**.

**Expected end-to-end UI latency (default settings):**
- **Best case:** ~`<1 second` (data arrives just before dashboard poll)
- **Typical:** ~`2–4 seconds`
- **Worst case:** ~`~5–7 seconds` (data arrives just after a poll and waits for next cycle)

### 3) Dashboard Update Frequency

- Dashboard updates from `/api/latest` every **5 seconds** (`POLL_INTERVAL_MS = 5000`).
- Effective update rate: **`0.2 Hz`**.

### 4) SQLite Storage Capacity (Retention Estimate)

At one saved row every 2 seconds:

- **Rows/day:** `86,400 / 2 = 43,200`
- **Rows/year:** `43,200 × 365 = 15,768,000`

Approximate disk usage is usually in the low MB/day range for this schema. A practical planning estimate is:

- **~4–7 MB/day** (depends on SQLite page usage and timestamp/value sizes)

Estimated retention by DB budget:

- **100 MB** → ~`14–25 days`
- **500 MB** → ~`71–125 days`
- **1 GB** → ~`143–250 days`

## Running Only The MQTT Subscriber

If you want to test MQTT ingestion without the Flask dashboard:

```bash
python3 Python/receiver.py
```

This connects to HiveMQ, subscribes to both environment topics, logs incoming messages, and stores complete temperature/humidity readings in SQLite.

## Dashboard-Only Testing

The dashboard folder includes [Dashboard/server_example.py](</Users/meydivyansh/Projects /SmartEnvironmentMonitor/Dashboard/server_example.py>) for local frontend testing. See [Dashboard/README.md](</Users/meydivyansh/Projects /SmartEnvironmentMonitor/Dashboard/README.md>) for that workflow.

## Troubleshooting

- If the dashboard shows `Waiting`, confirm the ESP32 is publishing to the same MQTT topics used in `Python/receiver.py`.
- If the dashboard shows `Offline`, make sure the Flask backend is running and `Dashboard/config.js` points to the correct API base URL.
- If no database rows are appearing, check that both temperature and humidity messages are being received.
- If using real hardware, replace `Wokwi-GUEST` with your actual Wi-Fi SSID and password.
- If using the public MQTT broker, choose unique topics if multiple people may be publishing test data at the same time.

## Learning Outcomes

This project demonstrates:

- ESP32 sensor programming
- DHT22 data collection
- Wi-Fi and MQTT communication
- Python MQTT callbacks
- Flask API development
- SQLite persistence
- CSV export
- Browser dashboards with Chart.js
- Full IoT data flow from device to UI

## Possible Improvements

- Add authentication for dashboard/API access
- Move MQTT broker and topic values into environment variables
- Add configurable alert rules from the backend
- Add notification channels for threshold alerts
- Add Docker support for easier deployment
- Deploy the Flask app and dashboard to a cloud server

## License

This project is available under the MIT License.
