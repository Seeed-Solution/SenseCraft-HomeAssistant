import logging

from homeassistant.core import HomeAssistant
import json
from .mqtt_client import MQTTClient
from ..const import (
    DOMAIN,
)
_LOGGER = logging.getLogger(__name__)


class WatcherLocal():

    def __init__(self, hass: HomeAssistant, config: dict):
        self.hass = hass
        self.deviceName = config.get('device_name')
        self.deviceId = config.get('device_id')

        self.mqttBroker = config.get('mqtt_broker')
        self.mqttPort = config.get('mqtt_port')
        self.mqttUsername = config.get('mqtt_username')
        self.mqttPassword = config.get('mqtt_password')
        self.mqttTopic = config.get('mqtt_topic')

        self.mqttClient = None
        self.connected = False

    def to_config(self):
        return {
            'device_name': self.deviceName,
            'device_id': self.deviceId,
            'mqtt_broker': self.mqttBroker,
            'mqtt_port': self.mqttPort,
            'mqtt_username': self.mqttUsername,
            'mqtt_password': self.mqttPassword,
            'mqtt_topic': self.mqttTopic,
        }

    @staticmethod
    def from_config(hass: HomeAssistant, config: dict):
        # 从字典创建对象
        local = WatcherLocal(hass, config)
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
                self.mqttClient.subscribe(self.mqttTopic)
                self.mqttClient.message_received = self.on_message
                self.connected = True
                return True

        except Exception as e:
            print('setMqtt failed', e)
            self.connected = False
            return False

    def stop(self):
        if self.mqttClient:
            self.mqttClient.loop_stop()
            self.mqttClient.disconnect()
            self.connected = False

    def on_message(self, msg):
        if msg.payload is not None:
            data = json.loads(msg.payload)
            eui = data.get('deviceEui')
            events = data.get('events')
            text = events.get('text')
            image = events.get('img')

            if text is not None:
                _event_type = ("{domain}_watcher_alarm_{eui}").format(
                    domain=DOMAIN,
                    eui=eui
                )
                self.hass.bus.fire(_event_type, {"text": text})

            if image is not None:
                _event_type = ("{domain}_watcher_image_{eui}").format(
                    domain=DOMAIN,
                    eui=eui
                )
                self.hass.bus.fire(_event_type, {"image": image})

            data = events.get('data')
            sensor = data.get('sensor')
            if sensor is not None:
                temperature = sensor.get('temperature')
                if temperature is not None:
                    _event_type = ("{domain}_watcher_temperature_{eui}").format(
                        domain=DOMAIN,
                        eui=eui,
                    )
                    self.hass.bus.fire(_event_type, {"value": temperature})

                humidity = sensor.get('humidity')
                if humidity is not None:
                    _event_type = ("{domain}_watcher_humidity_{eui}").format(
                        domain=DOMAIN,
                        eui=eui,
                    )
                    self.hass.bus.fire(_event_type, {"value": humidity})

                co2 = sensor.get('CO2')
                if co2 is not None:
                    _event_type = ("{domain}_watcher_co2_{eui}").format(
                        domain=DOMAIN,
                        eui=eui,
                    )
                    self.hass.bus.fire(_event_type, {"value": co2})
                
    
