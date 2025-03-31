import json
import logging
from homeassistant.core import HomeAssistant
from .mqtt_client import MQTTClient
from ..const import (
    DOMAIN,
)
_LOGGER = logging.getLogger(__name__)


class ReCamera():

    def __init__(self, hass: HomeAssistant, config: dict):
        self.hass = hass
        self.deviceName = config.get('device_name')
        self.deviceId = config.get('device_id')

        self.mqttBroker = config.get('mqtt_broker')
        self.mqttPort = config.get('mqtt_port')
        self.mqttUsername = config.get('mqtt_username')
        self.mqttPassword = config.get('mqtt_password')
        self.topic = ("sensecraft/recamera/{deviceId}/control").format(
            deviceId=self.deviceId
        )
        self.control_topic = f"sensecraft/recamera/{self.deviceId}/control"
        self.state_topic = f"sensecraft/recamera/{self.deviceId}/state"
        self.image_topic = f"sensecraft/recamera/{self.deviceId}/image"

        self.mqttClient = None
        self.connected = False
        self.classes = []
        self._state_callback = None
        self._image_callback = None

    def to_config(self):
        return {
            'device_name': self.deviceName,
            'device_id': self.deviceId,
            'mqtt_broker': self.mqttBroker,
            'mqtt_port': self.mqttPort,
            'mqtt_username': self.mqttUsername,
            'mqtt_password': self.mqttPassword,
        }

    @staticmethod
    def from_config(hass: HomeAssistant, config: dict):
        # 从字典创建对象
        local = ReCamera(hass, config)
        return local

    def setMqtt(self):
        try:
            mqtt = MQTTClient(
                self.mqttBroker,
                int(self.mqttPort),
                self.mqttUsername,
                self.mqttPassword
            )
            if mqtt.connect():
                self.mqttClient = mqtt
                # 订阅状态和图片主题
                self.mqttClient.subscribe(self.state_topic)
                self.mqttClient.subscribe(self.image_topic)
                self.mqttClient.message_received = self.received_message
                self.connected = True
                
                return True
        except Exception as e:
            _LOGGER.error('setMqtt failed: %s', e)
            self.connected = False
            return False

    def stop(self):
        """Stop all services."""
        # 停止 MQTT 客户端
        if self.mqttClient:
            self.mqttClient.loop_stop()
            self.mqttClient.disconnect()
            self.connected = False
        
            
    def send_control(self, data):
        """Send control command via MQTT."""
        if self.mqttClient and self.connected:
            self.mqttClient.publish(self.control_topic, json.dumps(data))

    def on_received_image(self, callback):
        """Set callback for image monitoring."""
        self._image_callback = callback

    def on_received_state(self, callback):
        """Set callback for state monitoring."""
        self._state_callback = callback

    def received_message(self, msg):
        """Handle received MQTT message."""
        try:
            # 检查消息 topic 是否匹配当前设备
            topic_parts = msg.topic.split('/')
            if len(topic_parts) < 3 or \
               topic_parts[0] != 'sensecraft' or \
               topic_parts[1] != 'recamera' or \
               topic_parts[2] != self.deviceId:
                _LOGGER.debug("Ignoring message from topic: %s", msg.topic)
                return

            # 根据主题类型处理消息
            if msg.topic == self.image_topic:
                # 处理图片数据
                if self._image_callback:
                    self._image_callback(msg.payload)
            elif msg.topic == self.state_topic:
                # 处理状态数据
                if self._state_callback:
                    self._state_callback(msg.payload)

        except Exception as e:
            _LOGGER.error("Error in received_message: %s", e)
    
