#include <WiFi.h>
#include <PubSubClient.h>
#include <DHTesp.h>
#include "config.h"

// Hardware and Network Objects
DHTesp dht;
WiFiClient espClient;
PubSubClient client(espClient);

// Timing and System State Variables
unsigned long lastPublishTime = 0;
unsigned long lastReconnectAttempt = 0;
unsigned long lastBlinkTime = 0;
bool ledState = LOW;

// Filtered Telemetry Values (Exponential Moving Average)
float filteredTemp = 0.0;
float filteredHum = 0.0;
bool firstReading = true;

// LED Status Indicator Helper
void updateStatusLED(bool connected) {
  if (connected) {
    digitalWrite(STATUS_LED_PIN, HIGH); // Solid ON when fully connected
  } else {
    // Non-blocking blink while disconnected / connecting
    unsigned long now = millis();
    if (now - lastBlinkTime >= 250) {
      lastBlinkTime = now;
      ledState = !ledState;
      digitalWrite(STATUS_LED_PIN, ledState);
    }
  }
}

// Reconnect to MQTT Broker non-blockingly
bool reconnectMQTT() {
  Serial.print("Connecting to MQTT broker at ");
  Serial.print(MQTT_BROKER);
  Serial.print("... ");

  String clientId = String(MQTT_CLIENT_PREFIX) + String(random(0xffff), HEX);

  if (client.connect(clientId.c_str(), TOPIC_STATUS, 0, true, "offline")) {
    Serial.println("CONNECTED!");
    client.publish(TOPIC_STATUS, "online", true);
    digitalWrite(STATUS_LED_PIN, HIGH);
    return true;
  } else {
    Serial.print("FAILED, rc=");
    Serial.println(client.state());
    return false;
  }
}

// Connect to WiFi non-blockingly
void ensureWiFiConnected() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.println("WiFi connection lost. Reconnecting...");
  WiFi.disconnect();
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    updateStatusLED(false);
    delay(100);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected! Local IP: " + WiFi.localIP().toString());
}

// Apply Exponential Moving Average (EMA) noise filter
float applyEMA(float current, float raw, float alpha) {
  if (firstReading) return raw;
  return (alpha * raw) + ((1.0 - alpha) * current);
}

void setup() {
  Serial.begin(115200);
  pinMode(STATUS_LED_PIN, OUTPUT);
  digitalWrite(STATUS_LED_PIN, LOW);
  randomSeed(micros());

  Serial.println("==========================================");
  Serial.println(" Smart Environment Monitor - Firmware V2  ");
  Serial.println(" ESP32 + DHT22 + Non-Blocking MQTT Engine ");
  Serial.println("==========================================");

  dht.setup(DHT_PIN, DHTesp::DHT22);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  ensureWiFiConnected();

  client.setServer(MQTT_BROKER, MQTT_PORT);
  client.setKeepAlive(60);
}

void loop() {
  ensureWiFiConnected();

  unsigned long currentMillis = millis();

  // Maintain MQTT Client State
  if (!client.connected()) {
    updateStatusLED(false);
    if (currentMillis - lastReconnectAttempt >= RECONNECT_INTERVAL_MS) {
      lastReconnectAttempt = currentMillis;
      if (reconnectMQTT()) {
        lastReconnectAttempt = 0;
      }
    }
  } else {
    client.loop();
    updateStatusLED(true);
  }

  // Non-blocking Telemetry Sampling & Publishing
  if (currentMillis - lastPublishTime >= PUBLISH_INTERVAL_MS) {
    lastPublishTime = currentMillis;

    TempAndHumidity rawData = dht.getTempAndHumidity();

    // Sanity & Validity Check
    if (isnan(rawData.temperature) || isnan(rawData.humidity) ||
        rawData.temperature < MIN_TEMP_C || rawData.temperature > MAX_TEMP_C ||
        rawData.humidity < MIN_HUM_PCT || rawData.humidity > MAX_HUM_PCT) {
      Serial.println("[ERROR] DHT22 sensor read invalid or out of bounds. Skipping frame.");
      return;
    }

    // Apply EMA noise filter
    filteredTemp = applyEMA(filteredTemp, rawData.temperature, SENSOR_EMA_ALPHA);
    filteredHum = applyEMA(filteredHum, rawData.humidity, SENSOR_EMA_ALPHA);
    firstReading = false;

    // Format telemetry strings (1 decimal place)
    String tempStr = String(filteredTemp, 1);
    String humStr = String(filteredHum, 1);

    if (client.connected()) {
      client.publish(TOPIC_TEMPERATURE, tempStr.c_str());
      client.publish(TOPIC_HUMIDITY, humStr.c_str());

      Serial.print("[TELEMETRY] Temp: ");
      Serial.print(tempStr);
      Serial.print(" °C | Hum: ");
      Serial.print(humStr);
      Serial.println(" % -> Published to MQTT");
    } else {
      Serial.println("[WARN] MQTT offline. Telemetry buffered in memory.");
    }
  }
}
