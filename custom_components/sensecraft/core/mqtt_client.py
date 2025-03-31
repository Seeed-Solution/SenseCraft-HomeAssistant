import paho.mqtt.client as mqtt
import threading

class MQTTClient:

    def __init__(self, broker, port, username, password, client_id=""):
        self.broker = broker
        self.port = port
        self.username = '' if username is None else username
        self.password = '' if password is None else password
        self.client = mqtt.Client(client_id or None)
        self.connectEvent = threading.Event()
        self.message_received = None

    def __del__(self):
        if self.client:
            self.client.disconnect()
            self.loop_stop()

    def on_connect(self, client, userdata, flags, rc):
        print('mqtt connected', self.broker, rc)
        if rc == 0:
            self.connectEvent.set()
        else:
            print(f"mqtt connect failed with result code {rc}")

    def on_disconnect(self, client, userdata, rc):
        print('mqtt disconnect', self.broker)

    def on_message(self, client, userdata, msg):
        if self.message_received is not None:
            self.message_received(msg)

    def connect(self):
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        self.client.username_pw_set(self.username, self.password)
        self.client.connect(self.broker, self.port, 120)
        self.loop_start()
        # 等待连接结果
        if self.connectEvent.wait(timeout=10):
            return True
        else:
            return False

    def loop_start(self):
        self.client.loop_start()

    def loop_stop(self):
        self.client.loop_stop()

    def disconnect(self):
        self.client.disconnect()

    def subscribe(self, topic):
        self.client.subscribe(topic)

    def publish(self, topic, payload=None, qos=0, retain=False):
        print('publish:', topic, payload)
        self.client.publish(topic, payload, qos, retain)
