#ifndef CONFIG_H
#define CONFIG_H

// WiFi Configuration
#define WIFI_SSID "Wokwi-GUEST"
#define WIFI_PASSWORD ""

// MQTT Broker Configuration
#define MQTT_BROKER "broker.hivemq.com"
#define MQTT_PORT 1883
#define MQTT_CLIENT_PREFIX "DivyanshESP32-"

// MQTT Topics
#define TOPIC_TEMPERATURE "divyansh/environment/temperature"
#define TOPIC_HUMIDITY "divyansh/environment/humidity"
#define TOPIC_STATUS "divyansh/environment/status"

// Hardware Pin Definitions
#define DHT_PIN 15
#define STATUS_LED_PIN 2

// System & Sampling Parameters
#define PUBLISH_INTERVAL_MS 2000     // Telemetry interval in milliseconds
#define RECONNECT_INTERVAL_MS 5000   // Reconnect wait interval
#define SENSOR_EMA_ALPHA 0.3         // Exponential Moving Average filter coefficient (0.0 to 1.0)

// Thresholds for Sensor Sanity Check
#define MIN_TEMP_C -20.0
#define MAX_TEMP_C 70.0
#define MIN_HUM_PCT 0.0
#define MAX_HUM_PCT 100.0

#endif // CONFIG_H
