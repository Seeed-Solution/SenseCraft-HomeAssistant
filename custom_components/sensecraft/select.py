from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from .core.jetson import Jetson
from .core.recamera import ReCamera
from .const import (
    DOMAIN,
    JETSON,
    DATA_SOURCE,
    RECAMERA_GIMBAL,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up stream select platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    data_source = data.get(DATA_SOURCE)
    if data_source == JETSON:
        local: Jetson = data[JETSON]
        jetsonStreamSelect = JetsonStreamSelect(local.deviceMac, local.deviceName, config_entry.entry_id)
        local.on_monitor_stream_list(jetsonStreamSelect.received_stream_list)
        async_add_entities([jetsonStreamSelect], False)
    elif data_source == RECAMERA_GIMBAL:
        recamera: ReCamera = data[RECAMERA_GIMBAL]
        trackTargetSelect = ReCameraTrackTargetSelect(recamera, config_entry.entry_id)
        async_add_entities([trackTargetSelect], False)



class JetsonStreamSelect(SelectEntity):
    def __init__(self, id: str, name: str, entry_id: str):
        """Initialize the select."""
        self._attr_unique_id = id
        self._entry_id = entry_id
        self._device_name = name
        self._attr_name = 'stream list'
        self._attr_options = []
        self._attr_current_option = None

    def received_stream_list(self, streams):
        self._attr_options = streams
        if self._attr_current_option is None and len(streams) > 0:
            self._attr_current_option = streams[0]
            data = self.hass.data[DOMAIN][self._entry_id]
            local: Jetson = data[JETSON]
            local.updateStream(streams[0])
        self.schedule_update_ha_state()
            

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._attr_unique_id)
            },
            name=self._device_name,
            manufacturer="Seeed Studio",
            model="Jetson",
            sw_version="1.0",
        )

    # @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return True

    @property
    def options(self):
        """Return a set of selectable options."""
        return self._attr_options
    
    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        self._attr_current_option = option
        data = self.hass.data[DOMAIN][self._entry_id]
        local: Jetson = data[JETSON]
        local.updateStream(option)
        self.async_schedule_update_ha_state()

    def should_poll():
        return True


class ReCameraTrackTargetSelect(SelectEntity):
    """Select entity for ReCamera track target."""

    def __init__(self, recamera: ReCamera, entry_id: str):
        """Initialize the track target select."""
        self._recamera = recamera
        self._entry_id = entry_id
        self._attr_name = f"{recamera.deviceName} Track Object Option"
        self._attr_unique_id = f"{recamera.deviceId}_track_target"
        self._attr_options = ["Person", "Car", "Cat", "Dog", "Bottle", "Cup", "Cell Phone"]
        self._attr_current_option = "Person"
        self._attr_icon = "mdi:crosshairs-gps"
        
        # 目标ID映射
        self._target_id_map = {
            "Person": 0,
            "Car": 2,
            "Cat": 15,
            "Dog": 16,
            "Bottle": 39,
            "Cup": 41,
            "Cell Phone": 67
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._recamera.deviceId)},
            name=self._recamera.deviceName,
            manufacturer="Seeed Studio",
            model="ReCamera",
            sw_version="1.0",
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._recamera.connected

    async def async_select_option(self, option: str) -> None:
        """Change the selected target for tracking."""
        self._attr_current_option = option
        # 获取选项对应的ID
        target_id = self._target_id_map.get(option, 0)
        
        # Send command to device with the target ID
        command = {
            "code": 0,
            "data": {
                "type": "tracking",
                "command": "set_target",
                "target_id": target_id
            }
        }
        self._recamera.send_control(command)
        self.async_schedule_update_ha_state()
