"""sensor platform."""
from __future__ import annotations
import json
import logging
import random
import paho.mqtt.client as mqtt
from .const import (
    DOMAIN,
    MEASUREMENT_DICT
)
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_CO2,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
)
from homeassistant.helpers.device_registry import (
    DeviceInfo,
    async_entries_for_config_entry,
    async_get
)
from homeassistant.helpers.entity import Entity
from requests import post
from .const import (
    DOMAIN,
    ORG_ID,
    ACCESS_ID,
    ACCESS_KEY,
    SELECTED_DEVICE,
    ACCOUNT_ENV,
    ENV_URL,
    OPENSTREAM,
    OPENAPI
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
) -> None:
    """Setup sensors from a config entry created in the integrations UI."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    
    orgID = data.get(ORG_ID)
    accessid = data.get(ACCESS_ID)
    accesskey = data.get(ACCESS_KEY)
    env = data.get(ACCOUNT_ENV)
    
    selectedDeviceEuis = data.get(SELECTED_DEVICE)

    async def getDeviceDetail(accessid: str, accesskey:str, deviceList, env):
        def list_device_channels(username: str, password: str, deviceList):
            url = ("{openapi}/list_device_channels").format(
                    openapi=ENV_URL[env][OPENAPI],
                )
            headers = {"Content-Type": "application/json"}
            response = post(url, headers=headers, auth=(username, password), data=json.dumps({"device_euis": deviceList}))
            resp = json.loads(response.text)
            data = resp.get('data')
            code = resp.get('code')
            if int(code) != 0 or data is None:
                raise ValueError
            return data
        try:
            response = await hass.async_add_executor_job(list_device_channels,accessid,accesskey,deviceList)
            return response
        except:
            raise ValueError
        
    if len(selectedDeviceEuis) > 0:
        selectedDeviceChannels = await getDeviceDetail(accessid,accesskey,list(selectedDeviceEuis),env)
    else :
        selectedDeviceChannels = []
    
    broker = ENV_URL[env][OPENSTREAM]
    device_registry = async_get(hass)
    devices = async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )
    all_device = {device.id: list(device.identifiers)[0][1] for device in devices}
    removed_devices = [
        device_id
        for device_id in all_device.keys()
        if all_device[device_id] not in selectedDeviceEuis
    ]
    for device_id in removed_devices:
        # Unregister from HA
        device_registry.async_remove_device(device_id)
    entities = []
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
                entities.append(Sensor(deviceInfo))
    # add entities to HA
    async_add_entities(entities, update_before_add=True)           
    
    topic = ("/device_sensor_data/{orgID}/#").format(
        orgID=orgID
    )
    client_id = ("org-{orgID}-{random}").format(
        orgID=orgID, random=random.randint(0, 1000)
    )
    username = ("org-{orgID}").format(
        orgID=orgID
    )

    def on_connect(client, userdata, flags, rc):
        print("on_connect",rc,topic)
        if rc == 0:
            client.subscribe(topic)
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code", rc)
            
    def on_disconnect(client, userdata, rc):
        print("Failed Connect")

    def on_message(client, userdata, msg):
        data = msg.payload.decode()
        print(f"Received `{data}` from `{msg.topic}` topic")
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
        if eui not in selectedDeviceEuis:
            return

        entity_id = ("{eui}_{channel_index}_{measurementID}").format(
                    eui=eui,
                    channel_index=channelIndex,
                    measurementID=measurementID
                )
        event_type = ("{domain}_mqtt_{id}").format(
            domain=DOMAIN,
            id=entity_id
        )
        hass.bus.fire(event_type, {"value": value})

    client = mqtt.Client(client_id, True)
    client.username_pw_set(username, accesskey)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, 1883, keepalive=120)
    client.on_disconnect = on_disconnect
    client.loop_start()

class Sensor(Entity):
    def __init__(self, deviceInfo: dict):
        """Initialize the sensor."""
        self._attr_unique_id = ("{eui}_{channel_index}_{measurementID}").format(
                    eui=deviceInfo['eui'],
                    channel_index=deviceInfo['channelIndex'],
                    measurementID=deviceInfo['measurementID']
                )
        self._event_type = ("{domain}_mqtt_{id}").format(
            domain=DOMAIN,
            id=self._attr_unique_id
        )
        self._uniform_type = deviceInfo['uniform_type']
        self._eui = deviceInfo['eui']
        deviceName = deviceInfo['name']
        if deviceName is None or len(deviceName) == 0:
            self._device_name = self._eui
        else:
            self._device_name = deviceName

        self._state = None
        self._event = None
        self._measurementID = deviceInfo['measurementID']
        measurementInfo = MEASUREMENT_DICT[self._measurementID]
        self._attr_name  = measurementInfo[0]
        self._attr_unit_of_measurement = measurementInfo[1]
        self._attr_icon = measurementInfo[2]

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        print('added_to_hass:',self._attr_unique_id)
        def handle_event(event):
            print('handle_event',event.data.get('value'))
            self._state = event.data.get('value')
            self.schedule_update_ha_state()
        self._event = self.hass.bus.async_listen(self._event_type, handle_event)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        print('will_remove_from_hass:',self._attr_unique_id)
        if self._event:
            self._event()
            self._event = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._eui)
            },
            name=self._device_name,
            manufacturer="SenseCraft",
            model="SenseCraft",
            sw_version="1.0",
        )
    
    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return self._state

    @property
    def state(self):
        return self._state
    
    def should_poll():
        return True
    