import json
import logging
from requests import get
from homeassistant.core import HomeAssistant
from .mqtt_client import MQTTClient
from ..const import (
    DOMAIN,
)
_LOGGER = logging.getLogger(__name__)

class SenseCraftLocal():

    def __init__(self, hass: HomeAssistant, config: dict):
        self.hass = hass
        self.deviceHost = config.get('device_host')
        self.devicePort = config.get('device_port', '1880')
        self.deviceName = config.get('device_name')
        self.deviceMac = config.get('device_mac')
        self.deviceType = config.get('device_type')

        self.mqttBroker = config.get('mqtt_broker')
        self.mqttPort = config.get('mqtt_port')
        self.mqttUsername = config.get('mqtt_username')
        self.mqttPassword = config.get('mqtt_password')
        self.topic = "/seeed/jetson/event"

        self.mqttClient = None
        self.stream_callback = None
        self.stream_list_callback = None
        self.current_stream = None
        self.connected = False

    def to_config(self):
        return {
            'device_host': self.deviceHost,
            'device_port': self.devicePort,
            'device_name': self.deviceName,
            'device_mac': self.deviceMac,
            'device_type': self.deviceType,
            'mqtt_broker': self.mqttBroker,
            'mqtt_port': self.mqttPort,
            'mqtt_username': self.mqttUsername,
            'mqtt_password': self.mqttPassword,
        }

    @staticmethod
    def from_config(hass: HomeAssistant, config: dict):
        # 从字典创建对象
        local = SenseCraftLocal(hass, config)
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
                self.mqttClient.subscribe(self.topic)
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
        if self.topic != msg.topic:
            return
        
        payload = msg.payload.decode()
        resp = json.loads(payload)
        mac = resp.get('mac')
        if mac != self.deviceMac:
            return
        name = resp.get('name')
        data = resp.get('data')
        if name == "inferenceResultEvent":
            streams = data.get('Streams')
            stream_name_list = []
            if streams is not None:
                for stream in streams:
                    # uuid = stream.get('uuid')
                    frame = stream.get('frame')
                    # results = stream.get('results')
                    info = stream.get('info')
                    stream_name = stream.get('stream_name')
                    stream_name_list.append(stream_name)
                    if stream_name == self.current_stream:
                        if self.stream_callback is not None:
                            self.stream_callback(frame)

                        for key in info:
                            if key !='timestamp':
                                _event_type = f"{DOMAIN}_inference_{mac}_{key}"
                                self.hass.bus.fire(_event_type, {"value": info[key]})

            if self.stream_list_callback is not None:
                self.stream_list_callback(stream_name_list)

        elif name == "deviceInfo":
            memoryUsed = data.get('memoryUsed')
            memoryTotal = data.get('memoryTotal')
            memoryUsed_type = f"{DOMAIN}_info_{mac}_memoryUsed"
            if memoryUsed>0 and memoryTotal>0:
                value = memoryUsed/memoryTotal
                self.hass.bus.fire(memoryUsed_type, {"value": round(value,2)})
            else:
                self.hass.bus.fire(memoryUsed_type, {"value": 0})
            
            sdUsed = data.get('sdUsed')
            sdTotal = data.get('sdTotal')
            sdUsed_type = f"{DOMAIN}_info_{mac}_sdUsed"
            if sdUsed>0 and sdTotal>0:
                value = sdUsed/sdTotal
                self.hass.bus.fire(sdUsed_type, {"value": round(value,2)})
            else:
                self.hass.bus.fire(sdUsed_type, {"value": 0})
            
            flashUsed = data.get('flashUsed')
            flashTotal = data.get('flashTotal')
            flashUsed_type = f"{DOMAIN}_info_{mac}_flashUsed"
            if flashUsed>0 and flashTotal>0:
                value = flashUsed/flashTotal
                self.hass.bus.fire(flashUsed_type, {"value": round(value,2)})
            else:
                self.hass.bus.fire(flashUsed_type, {"value": 0})

            cpuTemperature = data.get('cpuTemperature')
            cpuTemperature_type = f"{DOMAIN}_info_{mac}_cpuTemperature"
            self.hass.bus.fire(cpuTemperature_type, {"value": cpuTemperature})
            
            cpuUsed = data.get('cpuUsed')
            cpuUsed_type = f"{DOMAIN}_info_{mac}_cpuUsed"
            self.hass.bus.fire(cpuUsed_type, {"value": round(float(cpuUsed),2)})

    def on_monitor_stream(self, callback):
        if not self.connected:
            self.setMqtt()

        self.stream_callback = callback

    def on_monitor_stream_list(self, callback):
        if not self.connected:
            self.setMqtt()

        self.stream_list_callback = callback
        
    def updateStream(self, stream):
        self.current_stream = stream
    
    def _request(self,cmd):
        url = f"http://{self.deviceHost}:{self.devicePort}/data?cmd={cmd}"
        response = get(url)
        resp = json.loads(response.text)
        data = resp.get('data')
        code = resp.get('code')
        if int(code) != 0 or data is None:
            _LOGGER.warning(
                'request error while decrypting response of request to %s :%s', url, resp)
            raise ValueError
        return data
        
    async def getModel(self):
        try:
            response = await self.hass.async_add_executor_job(self._request, 'MODLE')
            return response
        except:
            raise ValueError
        
    async def getInfo(self):
        try:
            response = await self.hass.async_add_executor_job(self._request, 'INFO')
            return response
        except:
            raise ValueError    
        
