"""sensor platform."""
from __future__ import annotations

import asyncio
import json
import logging
from .const import (
    DOMAIN,
    MEASUREMENT_DICT
)
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .core.sensecraft_cloud import SenseCraftCloud
from .core.sensecraft_local import SenseCraftLocal
from .core.sscma_local import SScmaLocal
from homeassistant.const import (
    PERCENTAGE,
    TEMP_CELSIUS,
)
from homeassistant.helpers.device_registry import (
    DeviceInfo,
    async_entries_for_config_entry,
    async_get
)
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.components.select import SelectEntity
from homeassistant.const import Platform
from .const import (
    DOMAIN,
    SENSECRAFT_CLOUD,
    SENSECRAFT_LOCAL,
    SSCMA_LOCAL,
    DATA_SOURCE,
    CLOUD,
    SENSECRAFT,
    SSCMA,
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
        cloud: SenseCraftCloud = data[SENSECRAFT_CLOUD]
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

    elif data_source == SENSECRAFT:
        senseCraftLocal: SenseCraftLocal = data[SENSECRAFT_LOCAL]
        mac = senseCraftLocal.deviceMac
        deviceName = senseCraftLocal.deviceName
        models = await senseCraftLocal.getModel()
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
        cpuTemperature._attr_unit_of_measurement = TEMP_CELSIUS
        entities.append(cpuTemperature)

        async_add_entities(entities, update_before_add=False)

    elif data_source == SSCMA:
        sscmaLocal: SScmaLocal = data[SSCMA_LOCAL]
        deviceId = sscmaLocal.deviceId
        deviceName = sscmaLocal.deviceName

        def classes_callback(classes):
            asyncio.run(handle_classes_entity(classes))

        sscmaLocal.on_classes_update(classes_callback)

        async def handle_classes_entity(classes):
            all_entity = []
            old_entities = hass.data[DOMAIN].get(f"{config_entry.entry_id}_entities", [])
            old_all_classes = []
            for entity in old_entities:
                # entity 在 all_entity 中没有的需要删除
                old_all_classes.append(entity.name)
                if entity.entity_id is not None and entity.name not in classes:
                    await entity.async_remove(force_remove=True)
            for key in classes:
                # 如果 key 不在 old_all_entity 中说明需要添加，否则就是已经添加过的
                if key not in old_all_classes:
                    all_entity.append(InferenceResult(deviceId, deviceName, key))
            if len(all_entity) != 0:
                hass.data[DOMAIN][f"{config_entry.entry_id}_entities"] = all_entity
                async_add_entities(all_entity, update_before_add=False)

        await handle_classes_entity(sscmaLocal.device.model.classes)


class CloudSensor(Entity):
    def __init__(self, deviceInfo: dict):
        """Initialize the sensor."""
        self._attr_unique_id = ("{eui}_{channel_index}_{measurementID}").format(
            eui=deviceInfo['eui'],
            channel_index=deviceInfo['channelIndex'],
            measurementID=deviceInfo['measurementID']
        )
        self._event_type = ("{domain}_cloud_{id}").format(
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
        self._attr_name = measurementInfo[0]
        self._attr_unit_of_measurement = measurementInfo[1]
        self._attr_icon = measurementInfo[2]

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""

        def handle_event(event):
            self._state = event.data.get('value')
            self.schedule_update_ha_state()

        self._event = self.hass.bus.async_listen(
            self._event_type, handle_event)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
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

    def should_poll(self):
        return True


class JetsonDeviceInfo(Entity):
    def __init__(self, deviceId: str, name: str, type: str):
        """Initialize the sensor."""
        self._attr_unique_id = ("{id}_{type}").format(
            id=deviceId,
            type=type,
        )
        self._deviceId = deviceId
        self._event_type = ("{domain}_info_{id}").format(
            domain=DOMAIN,
            id=self._attr_unique_id
        )
        self._device_name = name
        self._attr_name = type
        self._state = 0
        self._event = None

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""

        def handle_event(event):
            self._state = event.data.get('value')
            self.schedule_update_ha_state()

        self._event = self.hass.bus.async_listen(
            self._event_type, handle_event)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        if self._event:
            self._event()
            self._event = None

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

    def should_poll(self):
        return True


class InferenceResult(Entity):
    def __init__(self, deviceId: str, deviceName: str, object: str):
        """Initialize the sensor."""
        self._attr_unique_id = ("{id}_{object}").format(
            id=deviceId,
            object=object.lower(),
        )
        self._deviceId = deviceId
        self._event_type = ("{domain}_inference_{id}").format(
            domain=DOMAIN,
            id=self._attr_unique_id
        )
        self._device_name = deviceName
        self._attr_name = object
        self._state = 0
        self._event = None

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""

        def handle_event(event):
            self._state = event.data.get('value')
            self.schedule_update_ha_state()

        self._event = self.hass.bus.async_listen(
            self._event_type, handle_event)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        if self._event:
            self._event()
            self._event = None

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

    def should_poll(self):
        return True
