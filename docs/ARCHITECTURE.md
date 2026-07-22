# System Architecture & Technical Specification

## 1. Overview
The **Smart Environment Monitor** is an end-to-end, multi-tier IoT telemetry pipeline designed to collect, process, filter, store, and visualize environmental parameters (Temperature and Humidity) in real time.

---

## 2. End-to-End System Block Diagram

```mermaid
graph TD
    subgraph Edge Layer [Hardware & Firmware]
        DHT22[DHT22 Sensor] -->|Digital Single-Bus| ESP32[ESP32 Microcontroller]
        ESP32 -->|EMA Noise Filter| ESP32_Processing[Telemetry Processing]
        ESP32_Processing -->|Non-blocking Publish| WiFi[Wi-Fi Interface]
    end

    subgraph Messaging Layer [MQTT Broker]
        WiFi -->|Port 1883 / QOS 0| MQTT[HiveMQ MQTT Broker]
    end

    subgraph Cloud Backend Layer [Python & Flask]
        MQTT -->|Paho MQTT Client| Subscriber[MQTT Listener Thread]
        Subscriber -->|Lock-Protected Queue| Storage[SQLite Database]
        Storage -->|Indexed Queries| REST[Flask REST API Engine]
    end

    subgraph Presentation Layer [Web Dashboard]
        REST -->|HTTP GET /api/latest| UI_Cards[Live Metric Cards & Alerts]
        REST -->|HTTP GET /api/history| UI_Chart[Chart.js Telemetry Graph]
        REST -->|HTTP GET /api/export/csv| UI_Export[CSV Download Engine]
    end
```

---

## 3. Firmware State Machine

```mermaid
stateDiagram-v2
    [*] --> PowerOn
    PowerOn --> WiFiConnecting: Init Hardware & Pins
    WiFiConnecting --> MQTTConnecting: Wi-Fi Connected
    WiFiConnecting --> WiFiConnecting: Wi-Fi Reconnect Backoff

    MQTTConnecting --> Operational: MQTT Connected & Subscribed
    MQTTConnecting --> MQTTConnecting: MQTT Reconnect Backoff

    state Operational {
        [*] --> Idle
        Idle --> SensorSampling: Interval Timer (2s)
        SensorSampling --> DataValidation: Read DHT22
        DataValidation --> EMAFiltering: Valid Reading
        DataValidation --> Idle: Sensor Error (Skip Frame)
        EMAFiltering --> MQTTPublish: Compute Moving Average
        MQTTPublish --> Idle: Publish Temp & Hum Topics
    }

    Operational --> WiFiConnecting: Wi-Fi Lost
    Operational --> MQTTConnecting: MQTT Connection Lost
```

---

## 4. Telemetry Data Flow & Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant ESP as ESP32 Firmware
    participant MQTT as MQTT Broker
    participant SUB as Python Subscriber
    participant DB as SQLite DB
    participant API as Flask REST API
    participant UI as Browser Dashboard

    ESP->>ESP: Read DHT22 & Apply EMA Filter
    ESP->>MQTT: Publish 'divyansh/environment/temperature' (24.5°C)
    ESP->>MQTT: Publish 'divyansh/environment/humidity' (58.2%)
    MQTT->>SUB: Forward MQTT Message Callbacks
    SUB->>SUB: Verify Pair Completion (Temp + Hum)
    SUB->>DB: INSERT INTO readings (timestamp, temp, hum)
    UI->>API: Poll GET /api/latest (Every 5s)
    API->>UI: Return JSON { temperature: 24.5, humidity: 58.2, status: "ok" }
    UI->>API: Poll GET /api/history (Every 10s)
    API->>DB: SELECT * FROM readings ORDER BY id DESC LIMIT 30
    DB->>API: Return Row Array
    API->>UI: Return JSON { history: [...] }
    UI->>UI: Re-render Chart.js & Sparklines
```

---

## 5. Security & Reliability Highlights
- **Sanity Bounds Filtering**: Firmware rejects DHT readings below $-20^\circ\text{C}$ or above $+70^\circ\text{C}$, and humidity outside $0 - 100\%$.
- **Thread Safety**: Python backend utilizes threading locks (`threading.Lock`) for concurrent access to memory buffers between MQTT receiver threads and Flask HTTP workers.
- **Database Optimization**: SQLite indexing on timestamp column (`idx_readings_timestamp`) ensures constant-time $O(\log N)$ historical data lookup.
