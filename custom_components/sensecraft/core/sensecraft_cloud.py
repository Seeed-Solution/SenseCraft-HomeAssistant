import json
import hashlib
from requests import get, post
import logging
import random
from homeassistant.core import HomeAssistant
from .mqtt_client import MQTTClient

from ..const import (
    DOMAIN,
    ENV_CHINA,
    ENV_GLOBAL,
)

PORTAL = "portal"
OPENAPI = "openapi"
OPENSTREAM = "openstream"

ENV_URL = {
    ENV_CHINA: {
        PORTAL: 'https://sensecap.seeed.cn/portalapi',
        OPENAPI: 'https://sensecap.seeed.cn/openapi',
        OPENSTREAM: 'sensecap-openstream.seeed.cn',
    },
    ENV_GLOBAL: {
        PORTAL: 'https://sensecap.seeed.cc/portalapi',
        OPENAPI: 'https://sensecap.seeed.cc/openapi',
        OPENSTREAM: 'sensecap-openstream.seeed.cc',
    }
}

_LOGGER = logging.getLogger(__name__)


class SenseCraftCloud():

    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.username = None
        self.password = None
        self.env = ENV_GLOBAL
        self.accessid = None
        self.accesskey = None
        self.orgID = None
        self.broker = None
        self.selectedDeviceEuis = []
        self.mqttClient = None


    def to_config(self):
        return {
            'username': self.username,
            'password': self.password,
            'env': self.env,
            'access_id': self.accessid,
            'access_key': self.accesskey,
            'org_id': self.orgID,
            'selected_device_euis': self.selectedDeviceEuis,
        }

    @staticmethod
    def from_config(hass: HomeAssistant, config: dict):
        # 从字典创建对象
        cloud = SenseCraftCloud(hass)
        cloud.username = config.get('username')
        cloud.password = config.get('password')
        cloud.env = config.get('env')
        cloud.accessid = config.get('access_id')
        cloud.accesskey = config.get('access_key')
        cloud.orgID = config.get('org_id')
        cloud.selectedDeviceEuis = config.get('selected_device_euis')
        cloud.broker = ENV_URL[cloud.env][OPENSTREAM]
        return cloud

    def _login(self, username, password, env):
        url = ("{portalurl}/user/login?account={account}&password={password}&origin=1").format(
            portalurl=ENV_URL[env][PORTAL],
            account=username,
            password=password
        )
        response = post(url=url)
        resp = json.loads(response.text)
        data = resp.get('data')
        code = resp.get('code')
        if int(code) != 0 or data is None:
            _LOGGER.warning(
                'login error while decrypting response of request to %s :%s', url, resp)
            raise ValueError
        return data

    def _getFixedAccess(self, token):
        headers = {
            'Authorization': token,
        }
        url = ("{portalurl}/organization/access/getFixedAccess").format(
            portalurl=ENV_URL[self.env][PORTAL],
        )
        response = get(url, headers=headers)
        resp = json.loads(response.text)
        data = resp.get('data')
        code = resp.get('code')
        if int(code) != 0 or data is None:
            _LOGGER.warning(
                'getFixedAccess error while decrypting response of request to %s :%s', url, resp)
            raise ValueError
        return data

    async def senseCraftAuth(self, username, password, env):
        try:
            hash_object = hashlib.md5(password.encode('utf-8'))
            md5_password = hash_object.hexdigest()
            userdata = await self.hass.async_add_executor_job(self._login, username, md5_password, env)
            self.username = username
            self.password = md5_password
            self.env = env
            token = userdata.get('token')
            org_id = userdata.get('org_id')
            self.orgID = org_id
            apikey = await self.hass.async_add_executor_job(self._getFixedAccess, token)
            self.accessid = apikey.get("access_id")
            self.accesskey = apikey.get("access_key")
            self.broker = ENV_URL[env][OPENSTREAM]
            return True
        except:
            raise ValueError

    def _list_devices(self, username, password):
        url = ("{openapi}/list_devices").format(
            openapi=ENV_URL[self.env][OPENAPI],
        )
        response = get(url, auth=(username, password))
        resp = json.loads(response.text)
        data = resp.get('data')
        code = resp.get('code')
        if int(code) != 0 or data is None:
            _LOGGER.warning(
                'list_devices error while decrypting response of request to %s :%s', url, resp)
            raise ValueError
        return data

    async def getDeviceList(self):
        try:
            response = await self.hass.async_add_executor_job(self._list_devices, self.accessid, self.accesskey)
            return response
        except:
            raise ValueError

    def _list_device_channels(self, username, password, deviceList):
        url = ("{openapi}/list_device_channels").format(
            openapi=ENV_URL[self.env][OPENAPI],
        )
        headers = {"Content-Type": "application/json"}
        response = post(url, headers=headers, auth=(
            username, password), data=json.dumps({"device_euis": deviceList}))
        resp = json.loads(response.text)
        data = resp.get('data')
        code = resp.get('code')
        if int(code) != 0 or data is None:
            _LOGGER.warning(
                '_list_device_channels error while decrypting response of request to %s :%s', url, resp)
            raise ValueError
        return data

    async def getDeviceDetail(self, deviceList):
        try:
            response = await self.hass.async_add_executor_job(self._list_device_channels, self.accessid, self.accesskey, deviceList)
            return response
        except:
            raise ValueError

    async def getSelectedDeviceInfo(self):
        try:
            allDeviceList = await self.getDeviceList()
            allDevice_euis = [device.get('device_eui')
                              for device in allDeviceList]
            newSelectedDeviceEuis = [
                eui for eui in self.selectedDeviceEuis if eui in allDevice_euis]

            if len(newSelectedDeviceEuis) > 0:
                selectedDeviceChannels = await self.getDeviceDetail(list(newSelectedDeviceEuis))
            else:
                selectedDeviceChannels = []
            self.selectedDeviceEuis = newSelectedDeviceEuis

            deviceInfoList = []
            for device in selectedDeviceChannels:
                deviceInfo = dict()
                eui = device.get('device_eui')
                device_name = device.get('device_name')
                uniform_type = device.get('uniform_type')
                deviceInfo['eui'] = eui
                deviceInfo['name'] = device_name
                deviceInfo['uniform_type'] = uniform_type

                channels = device.get('channels')
                for channel in channels:
                    channelIndex = int(channel.get('channel_index'))
                    deviceInfo['channelIndex'] = channelIndex
                    measurement_ids = channel.get('measurement_ids')
                    for measurementID in measurement_ids:
                        deviceInfo['measurementID'] = measurementID
                        deviceInfoList.append(deviceInfo)
            return deviceInfoList
        except:
            raise []

    def received_message(self, msg):
        data = msg.payload.decode()
        topic = msg.topic
        data = json.loads(data)
        value = data.get('value')
        if value is None:
            return
        item = topic.split("/")
        if len(item) != 7:
            return
        eui = item[3]
        channelIndex = item[4]
        measurementID = item[6]
        if eui not in self.selectedDeviceEuis:
            return

        entity_id = f"{eui}_{channelIndex}_{measurementID}"
        event_type = f"{DOMAIN}_cloud_{entity_id}"
        self.hass.bus.fire(event_type, {"value": value})

    async def mqttConnect(self):
        try:
            client_id = f"org-{self.orgID}-{random.randint(0, 1000)}"
            username = f"org-{self.orgID}"
            topic = f"/device_sensor_data/{self.orgID}/#"
            self.mqttClient = MQTTClient(
                self.broker, 1883, username, self.accesskey, client_id)

            if self.mqttClient.connect():
                print("connect cloud successfully.")
                self.mqttClient.subscribe(topic)
                self.mqttClient.message_received = self.received_message
                return True
            print("connect cloud failed.")
            return False
        except:
            return False
    def stop(self):
        if self.mqttClient:
            self.mqttClient.loop_stop()
            self.mqttClient.disconnect()
            self.connected = False
