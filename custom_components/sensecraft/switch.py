"""Switch platform for ReCamera tracking control."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from .core.recamera import ReCamera
from .const import (
    DOMAIN,
    DATA_SOURCE,
    RECAMERA_GIMBAL,
)
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the ReCamera switch from a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    data_source = data.get(DATA_SOURCE)
    
    if data_source == RECAMERA_GIMBAL:
        recamera: ReCamera = data[RECAMERA_GIMBAL]
        tracking_switch = ReCameraTrackingSwitch(recamera)
        async_add_entities([tracking_switch], False)


class ReCameraTrackingSwitch(SwitchEntity):
    """Representation of a ReCamera tracking switch."""

    def __init__(self, recamera: ReCamera):
        """Initialize the tracking switch entity."""
        self._recamera = recamera
        self._attr_name = f"{recamera.deviceName} Target Track Enable"
        self._attr_unique_id = f"{recamera.deviceId}_tracking_enable"
        self._attr_icon = "mdi:crosshairs"
        self._attr_is_on = False
        
        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, recamera.deviceId)},
            name=recamera.deviceName,
            manufacturer="Seeed Studio",
            model="ReCamera",
            sw_version="1.0",
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._recamera.connected

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on tracking."""
        command = {
            "code": 0,
            "data": {
                "type": "tracking",
                "command": "enable",
                "value": True
            }
        }
        self._recamera.send_control(command)
        self._attr_is_on = True
        self.async_schedule_update_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off tracking."""
        command = {
            "code": 0,
            "data": {
                "type": "tracking",
                "command": "enable",
                "value": False
            }
        }
        self._recamera.send_control(command)
        self._attr_is_on = False
        self.async_schedule_update_ha_state()