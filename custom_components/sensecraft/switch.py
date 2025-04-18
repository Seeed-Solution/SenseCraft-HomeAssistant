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
    RECAMERA,
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

    if data_source == RECAMERA:
        recamera: ReCamera = data[RECAMERA]
        tracking_switch = ReCameraTrackSwitch(recamera)
        async_add_entities([tracking_switch], False)


class ReCameraTrackSwitch(SwitchEntity):
    """Representation of a ReCamera tracking switch."""

    def __init__(self, recamera: ReCamera):
        """Initialize the tracking switch entity."""
        self._recamera = recamera
        self._attr_name = f"{recamera.deviceName} Target Track Enable"
        self._attr_unique_id = f"{recamera.deviceId}_tracking_enable"
        self._attr_icon = "mdi:crosshairs"
        self._attr_is_on = False
        self._event_type = f"sensecraft_recamera_{self._attr_unique_id}"
        self._event = None
        self._connection_event = None

        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, recamera.deviceId)},
            name=recamera.deviceName,
            manufacturer="Seeed Studio",
            model="ReCamera",
            sw_version="1.0",
        )

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self._event = self.hass.bus.async_listen(
            self._event_type, self._handle_state_event)
        
        # 添加连接状态事件监听
        self._connection_event = self.hass.bus.async_listen(
            f"sensecraft_recamera_{self._recamera.deviceId}_connection_state",
            self._handle_connection_state
        )

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        if self._event:
            self._event()
            self._event = None
        
        if self._connection_event:
            self._connection_event()
            self._connection_event = None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._recamera.connected
    
    def _handle_connection_state(self, event):
        """Handle connection state changes."""
        self._recamera.connected = event.data.get("connected", False)
        self.hass.loop.call_soon_threadsafe(self.async_schedule_update_ha_state)
    
    async def _handle_state_event(self, event):
        """处理状态事件"""
        try:
            state_data = event.data.get("data", {})
            value = state_data.get("value")
            self._attr_is_on = value
            self.hass.loop.call_soon_threadsafe(self.async_schedule_update_ha_state)
        except Exception as e:
            _LOGGER.error("Error handling state event: %s", e)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on tracking."""
        command = {
            "command": "tracking_enable",
            'param': {
                "value": True
            }
        }

        result = await self._recamera.send_control(command)
        if result and result.get('code') == 0:
            self._attr_is_on = True
            self.async_schedule_update_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off tracking."""
        command = {
            "command": "tracking_enable",
            'param': {
                "value": False
            }
        }
        result = await self._recamera.send_control(command)
        if result and result.get('code') == 0:
            self._attr_is_on = False
            self.async_schedule_update_ha_state()
        
