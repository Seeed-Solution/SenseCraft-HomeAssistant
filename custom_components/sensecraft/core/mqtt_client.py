import paho.mqtt.client as mqtt
import threading
import logging

_LOGGER = logging.getLogger(__name__)


class MQTTClient:
    """MQTT client implementation using paho-mqtt VERSION2 API."""

    def __init__(self, broker, port, username, password, client_id=""):
        self.broker = broker
        self.port = port
        self.username = '' if username is None else username
        self.password = '' if password is None else password

        # Create client with VERSION2 API
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id or None,
        )
        self.connectEvent = threading.Event()
        self.message_received = None

    def __del__(self):
        """Cleanup when object is destroyed."""
        if self.client:
            self.client.disconnect()
            self.loop_stop()

    def on_connect(self, client, userdata, flags, reason_code, properties):
        """Callback for when the client connects to the broker."""
        if reason_code == 0:
            _LOGGER.info("MQTT connected to broker %s", self.broker)
            self.connectEvent.set()
        else:
            _LOGGER.error(
                "MQTT connection failed with result code %d", reason_code)

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        _LOGGER.info("MQTT disconnected from broker %s", self.broker)

    def on_message(self, client, userdata, message):
        if self.message_received is not None:
            self.message_received(message)

    def connect(self):
        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        # Set credentials if provided
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        # Connect to broker
        self.client.connect(self.broker, self.port, keepalive=120)
        self.loop_start()

        # Wait for connection result
        if self.connectEvent.wait(timeout=10):
            return True
        else:
            return False

    def loop_start(self):
        """Start the network loop in a separate thread."""
        self.client.loop_start()

    def loop_stop(self):
        """Stop the network loop."""
        self.client.loop_stop()

    def disconnect(self):
        """Disconnect from the broker."""
        self.client.disconnect()

    def subscribe(self, topic, qos=0):
        """Subscribe to a topic."""
        self.client.subscribe(topic, qos=qos)

    def publish(self, topic, payload=None, qos=0, retain=False):
        """Publish a message to a topic."""
        _LOGGER.debug("Publishing to %s: %s", topic, payload)
        self.client.publish(topic, payload, qos=qos, retain=retain)
