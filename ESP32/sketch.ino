#include <PubSubClient.h>
#include <WiFi.h>
#include <DHTesp.h>

const char* ssid = "Wokwi-GUEST";
const char* password = "";
const char* mqtt_server = "broker.hivemq.com";
const char* topic_temperature = "divyansh/environment/temperature";
const char* topic_humidity = "divyansh/environment/humidity";

const int DHT_PIN = 15;
const int PUBLISH_INTERVAL_MS = 2000;

DHTesp dht;

WiFiClient espClient;
PubSubClient client(espClient);

void reconnect() {

  while (!client.connected()) {

    Serial.print("Connecting to MQTT...");

    String clientId = "DivyanshESP32-" + String(random(1000, 9999));

    if (client.connect(clientId.c_str())) {

      Serial.println(" Connected!");

    } else {

      Serial.print(" Failed, rc=");
      Serial.println(client.state());

      delay(2000);

    }

  }

}

void setup() {

  Serial.begin(115200);
  randomSeed(micros());

  dht.setup(DHT_PIN, DHTesp::DHT22);

  Serial.println("Connecting to WiFi...");

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi Connected!");

  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
  client.setServer(mqtt_server, 1883);
  client.setKeepAlive(60);
  
}

void loop() {

  if (!client.connected()) {
    reconnect();
  }

  client.loop();

  TempAndHumidity data = dht.getTempAndHumidity();

  if (isnan(data.temperature) || isnan(data.humidity)) {
    Serial.println("DHT read failed; skipping publish.");
    delay(PUBLISH_INTERVAL_MS);
    return;
  }

  String temp = String(data.temperature, 1);
  client.publish(topic_temperature, temp.c_str());

  String hum = String(data.humidity, 1);
  client.publish(topic_humidity, hum.c_str());

  Serial.print("Temperature: ");
  Serial.print(data.temperature);
  Serial.println(" °C");

  Serial.print("Humidity: ");
  Serial.print(data.humidity);
  Serial.println(" %");

  Serial.println("----------------------------");

  delay(PUBLISH_INTERVAL_MS);
}
