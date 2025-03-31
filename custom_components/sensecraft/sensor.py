"""sensor platform."""
from __future__ import annotations
import json
import logging
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .core.cloud import Cloud
from .core.jetson import Jetson
from .core.grove_vision_ai_v2 import GroveVisionAiV2
from .core.watcher import Watcher
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.helpers.device_registry import (
    DeviceInfo,
    async_entries_for_config_entry,
    async_get
)
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import Entity
from .const import (
    MEASUREMENT_DICT,
    DOMAIN,
    CLOUD,
    JETSON,
    DATA_SOURCE,
    GROVE_VISION_AI_V2,
    WATCHER
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
) -> None:
    """Setup sensors from a config entry created in the integrations UI."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    data_source = data.get(DATA_SOURCE)

    if data_source == CLOUD:
        cloud: Cloud = data[CLOUD]
        deviceInfoList = await cloud.getSelectedDeviceInfo()

        selectedDeviceEuis = cloud.selectedDeviceEuis
        device_registry = async_get(hass)
        devices = async_entries_for_config_entry(
            device_registry, config_entry.entry_id
        )
        all_device = {device.id: list(device.identifiers)[
            0][1] for device in devices}
        removed_devices = [
            device_id
            for device_id in all_device.keys()
            if all_device[device_id] not in selectedDeviceEuis
        ]
        for device_id in removed_devices:
            # Unregister from HA
            device_registry.async_remove_device(device_id)

        entities = []
        for deviceInfo in deviceInfoList:
            entities.append(CloudSensor(deviceInfo))
        # add entities to HA
        async_add_entities(entities, update_before_add=True)
        await cloud.mqttConnect()

    elif data_source == JETSON:
        jetson: Jetson = data[JETSON]
        mac = jetson.deviceMac
        deviceName = jetson.deviceName
        models = await jetson.getModel()
        entities = []
        for key in models:
            result = InferenceResult(mac, deviceName, models[key])
            entities.append(result)

        memoryUsed = JetsonDeviceInfo(mac, deviceName, 'memoryUsed')
        memoryUsed._attr_unit_of_measurement = PERCENTAGE
        memoryUsed._attr_icon = "mdi:memory"
        entities.append(memoryUsed)

        sdUsed = JetsonDeviceInfo(mac, deviceName, 'sdUsed')
        sdUsed._attr_unit_of_measurement = PERCENTAGE
        sdUsed._attr_icon = "mdi:sd"
        entities.append(sdUsed)

        flashUsed = JetsonDeviceInfo(mac, deviceName, 'flashUsed')
        flashUsed._attr_unit_of_measurement = PERCENTAGE
        flashUsed._attr_icon = "mdi:memory"
        entities.append(flashUsed)

        cpuUsed = JetsonDeviceInfo(mac, deviceName, 'cpuUsed')
        cpuUsed._attr_unit_of_measurement = PERCENTAGE
        cpuUsed._attr_icon = "mdi:percent"
        entities.append(cpuUsed)

        cpuTemperature = JetsonDeviceInfo(mac, deviceName, 'cpuTemperature')
        cpuTemperature._attr_unit_of_measurement = UnitOfTemperature.CELSIUS
        entities.append(cpuTemperature)

        async_add_entities(entities, update_before_add=False)

    elif data_source == GROVE_VISION_AI_V2:
        groveVisionAiV2: GroveVisionAiV2 = data[GROVE_VISION_AI_V2]
        deviceId = groveVisionAiV2.deviceId
        deviceName = groveVisionAiV2.deviceName
        classes = groveVisionAiV2.classes
        entities = []
        for key in classes:
            result = InferenceResult(deviceId, deviceName, key)
            entities.append(result)
        async_add_entities(entities, update_before_add=False)

    elif data_source == WATCHER:
        watcher: Watcher = data[WATCHER]
        eui = watcher.deviceId
        entities = []

        temperature = WatcherSensor(eui, 'temperature')
        temperature._attr_name = "Temperature"
        temperature._attr_unit_of_measurement = UnitOfTemperature.CELSIUS
        temperature._attr_icon = "mdi:temperature-celsius"

        entities.append(temperature)

        humidity = WatcherSensor(eui, 'humidity')

        humidity._attr_name = "Air Humidity"
        humidity._attr_unit_of_measurement = "% RH",
        humidity._attr_icon = "mdi:water-percent"
        entities.append(humidity)

        co2 = WatcherSensor(eui, 'co2')
        co2._attr_name = "CO2"
        co2._attr_unit_of_measurement = "ppm",
        co2._attr_icon = "mdi:molecule-co2"
        entities.append(co2)

        alarm = AlarmSensor(eui)
        alarm._attr_name = "Alarm"
        alarm._attr_icon = "mdi:alarm-light"
        entities.append(alarm)

        async_add_entities(entities, update_before_add=False)


class CloudSensor(Entity):
    def __init__(self, deviceInfo: dict):
        """Initialize the sensor."""
        self._eui = deviceInfo['eui']
        self._attr_unique_id = f"{self._eui}_{deviceInfo['channelIndex']}_{deviceInfo['measurementID']}"
        self._event_type = f"{DOMAIN}_cloud_{self._attr_unique_id}"
        self._uniform_type = deviceInfo['uniform_type']
        
        deviceName = deviceInfo['name']
        if deviceName is None or len(deviceName) == 0:
            self._device_name = self._eui
        else:
            self._device_name = deviceName

        self._state = 'unavailable'
        self._event = None
        self._measurementID = deviceInfo['measurementID']
        measurementInfo = MEASUREMENT_DICT.get(self._measurementID)
        if measurementInfo is None:
            default_name = "Unknown Measurement"
            default_unit = None
            default_icon = "mdi:alert-circle-outline"
            measurementInfo = (default_name, default_unit, default_icon)
        self._attr_name = measurementInfo[0]
        self._attr_unit_of_measurement = measurementInfo[1]
        self._attr_icon = measurementInfo[2]

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        self._event = self.hass.bus.async_listen(
            self._event_type, self.handle_event)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        if self._event:
            self._event()
            self._event = None

    def handle_event(self, event):
        self._state = event.data.get('value')
        self.hass.async_create_task(self.async_write_ha_state())

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._eui)
            },
            name=self._device_name,
            manufacturer="Seeed Studio",
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


class JetsonDeviceInfo(Entity):
    def __init__(self, deviceId: str, name: str, type: str):
        """Initialize the sensor."""
        self._attr_unique_id = f"{deviceId}_{type}"
        self._deviceId = deviceId
        self._event_type = f"{DOMAIN}_info_{self._attr_unique_id}"
        self._device_name = name
        self._attr_name = type
        self._state = 'unavailable'
        self._event = None

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        self._event = self.hass.bus.async_listen(
            self._event_type, self.handle_event)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        if self._event:
            self._event()
            self._event = None

    def handle_event(self, event):
        self._state = event.data.get('value')
        self.hass.async_create_task(self.async_write_ha_state())

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._deviceId)
            },
            name=self._device_name,
            manufacturer="Seeed Studio",
            model="Jetson",
            sw_version="1.0",
        )

    @property
    def state(self):
        return self._state

    def should_poll():
        return True


class InferenceResult(Entity):
    def __init__(self, deviceId: str, deviceName: str, object: str):
        """Initialize the sensor."""
        self._attr_unique_id = f"{deviceId}_{object.lower()}"
        self._deviceId = deviceId
        self._event_type = f"{DOMAIN}_inference_{self._attr_unique_id}"
        self._device_name = deviceName
        self._attr_name = object
        self._state = 'unavailable'
        self._event = None

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        self._event = self.hass.bus.async_listen(
            self._event_type, self.handle_event)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        if self._event:
            self._event()
            self._event = None

    def handle_event(self, event):
        self._state = event.data.get('value')
        self.hass.async_create_task(self.async_write_ha_state())

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self._deviceId)
            },
            name=self._device_name,
            manufacturer="Seeed Studio",
            sw_version="1.0",
        )

    @property
    def state(self):
        return self._state

    def should_poll():
        return True


class WatcherSensor(Entity):
    def __init__(self, eui: str, type: str):
        """Initialize the sensor."""
        self._eui = eui
        self._attr_unique_id = f"watcher_{type}_{eui}"
        self._event_type = f"{DOMAIN}_{self._attr_unique_id}"
        self._attr_name = type
        self._state = 'unavailable'
        self._event = None

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        self._event = self.hass.bus.async_listen(
            self._event_type, self.handle_event)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        if self._event:
            self._event()
            self._event = None

    def handle_event(self, event):
        self._state = event.data.get('value')
        self.hass.async_create_task(self.async_write_ha_state())

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._eui)
            },
            name=self._eui,
            manufacturer="Seeed Studio",
            model="Watcher",
            sw_version="1.0",
        )

    @property
    def state(self):
        return self._state


class AlarmSensor(Entity):
    def __init__(self, eui: str):
        """Initialize the sensor."""
        self._eui = eui
        self._attr_unique_id = f"watcher_alarm_{eui}"
        self._event_type = f"{DOMAIN}_{self._attr_unique_id}"
        self._attr_name = type
        self._state = 'unavailable'
        self._event = None

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        self._event = self.hass.bus.async_listen(
            self._event_type, self.handle_event)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        if self._event:
            self._event()
            self._event = None

    def handle_event(self, event):
        self._state = event.data.get('text')
        self.hass.async_create_task(self.async_write_ha_state())

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._eui)
            },
            name="Alarm Sensor",
            manufacturer="Seeed Studio",
            model="Watcher",
            sw_version="1.0",
        )

    @property
    def state(self):
        return self._state
