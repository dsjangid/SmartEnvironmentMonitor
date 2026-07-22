import json
import logging
import signal
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, Dict, Optional

import paho.mqtt.client as mqtt

from database import get_recent_readings, init_db, save_reading

BROKER = "broker.hivemq.com"
PORT = 1883

TOPIC_TEMP = "divyansh/environment/temperature"
TOPIC_HUM = "divyansh/environment/humidity"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


class EnvironmentSubscriber:
    """Receives sensor readings from MQTT and stores the latest values."""

    def __init__(self) -> None:
        init_db()

        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id="smart-env-subscriber",
            protocol=mqtt.MQTTv311,
        )
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        self.latest_readings: Dict[str, Any] = {
            "temperature": None,
            "humidity": None,
            "timestamp": None,
        }
        self._updated_fields: set[str] = set()
        self._lock = Lock()
        self._running = True
        self._callbacks: Dict[str, Callable[[Dict[str, Any]], None]] = {}

    def on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        if reason_code != 0:
            logging.error("MQTT connection failed with code %s", reason_code)
            return

        logging.info("Connected to MQTT broker")
        client.subscribe([(TOPIC_TEMP, 0), (TOPIC_HUM, 0)])
        logging.info("Subscribed to %s and %s", TOPIC_TEMP, TOPIC_HUM)

    def on_message(self, client, userdata, msg) -> None:
        payload = msg.payload.decode("utf-8", errors="replace").strip()
        logging.info("Received from %s: %s", msg.topic, payload)

        value = self._parse_payload(payload, msg.topic)
        if value is None:
            return

        with self._lock:
            if msg.topic == TOPIC_TEMP:
                self.latest_readings["temperature"] = value
                self._updated_fields.add("temperature")
            elif msg.topic == TOPIC_HUM:
                self.latest_readings["humidity"] = value
                self._updated_fields.add("humidity")
            else:
                logging.warning("Unexpected topic: %s", msg.topic)
                return

            self.latest_readings["timestamp"] = datetime.now(timezone.utc).isoformat()

            if {"temperature", "humidity"}.issubset(self._updated_fields):
                save_reading(
                    float(self.latest_readings["temperature"]),
                    float(self.latest_readings["humidity"]),
                )
                self._updated_fields.clear()

        self.print_summary()
        self._notify_listeners()

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties) -> None:
        logging.warning("Disconnected from MQTT broker (reason: %s)", reason_code)

    def _parse_payload(self, payload: str, topic: str) -> Optional[float]:
        try:
            return float(payload)
        except ValueError:
            pass

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            logging.warning("Unable to parse payload: %s", payload)
            return None

        if isinstance(parsed, dict):
            if topic == TOPIC_TEMP and "temperature" in parsed:
                return float(parsed["temperature"])
            if topic == TOPIC_HUM and "humidity" in parsed:
                return float(parsed["humidity"])

        if isinstance(parsed, (int, float)):
            return float(parsed)

        logging.warning("Unsupported payload format: %s", payload)
        return None

    def print_summary(self) -> None:
        with self._lock:
            temp = self.latest_readings["temperature"]
            hum = self.latest_readings["humidity"]
        logging.info("Latest readings -> Temperature: %s°C, Humidity: %s%%", temp, hum)

    def register_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        self._callbacks[callback.__name__] = callback

    def _notify_listeners(self) -> None:
        readings = self.get_latest_readings()
        for callback in self._callbacks.values():
            callback(readings)

    def get_latest_readings(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self.latest_readings)

    def get_history(self, limit: int = 30) -> list[dict]:
        return get_recent_readings(limit=limit)

    def start(self) -> None:
        logging.info("Connecting to %s:%s", BROKER, PORT)
        self.client.connect(BROKER, PORT, keepalive=60)
        self.client.loop_forever(retry_first_connection=True)

    def stop(self) -> None:
        self._running = False
        self.client.disconnect()


def handle_shutdown(signum, frame) -> None:
    raise KeyboardInterrupt


def main() -> None:
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    subscriber = EnvironmentSubscriber()
    try:
        subscriber.start()
    except KeyboardInterrupt:
        logging.info("Stopping subscriber")
    finally:
        subscriber.stop()


if __name__ == "__main__":
    main()
