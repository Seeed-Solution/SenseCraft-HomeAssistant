from homeassistant.components.select import SelectEntity
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
    """Set up stream select platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    data_source = data.get(DATA_SOURCE)
    if data_source == RECAMERA:
        recamera: ReCamera = data[RECAMERA]
        trackTargetSelect = ReCameraTrackSelect(
            recamera, config_entry.entry_id)
        async_add_entities([trackTargetSelect], False)
        

class ReCameraTrackSelect(SelectEntity):
    """Select entity for ReCamera track target."""

    def __init__(self, recamera: ReCamera, entry_id: str):
        """Initialize the track target select."""
        self._recamera = recamera
        self._entry_id = entry_id
        self._attr_name = f"{recamera.deviceName} Track Object Option"
        self._attr_unique_id = f"{recamera.deviceId}_tracking_target"
        self._attr_options = ["Person", "Car", "Cat",
                              "Dog", "Bottle", "Cup", "Cell Phone"]
        self._attr_current_option = "Person"
        self._attr_icon = "mdi:crosshairs-gps"
        self._event_type = f"sensecraft_recamera_{self._attr_unique_id}"
        self._event = None
        self._connection_event = None

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
        self._id_to_target_map = {v: k for k, v in self._target_id_map.items()}

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

    def _handle_connection_state(self, event):
        """Handle connection state changes."""
        self._recamera.connected = event.data.get("connected", False)
        self.hass.loop.call_soon_threadsafe(self.async_schedule_update_ha_state)

    async def _handle_state_event(self, event):
        """处理状态事件"""
        try:
            state_data = event.data.get("data", {})
            target_id = state_data.get("target_id")
            option = self._id_to_target_map.get(target_id)
            self._attr_current_option = option
            self.hass.loop.call_soon_threadsafe(
                self.async_schedule_update_ha_state)
        except Exception as e:
            _LOGGER.error("Error handling state event: %s", e)

    async def async_select_option(self, option: str) -> None:
        """Change the selected target for tracking."""
        self._attr_current_option = option
        # 获取选项对应的ID
        target_id = self._target_id_map.get(option, 0)

        # Send command to device with the target ID

        command = {
            "command": "tracking_target",
            'param': {
                'target_id': target_id
            }
        }
        result = await self._recamera.send_control(command)
        if result and result.get('code') == 0:
            self.async_schedule_update_ha_state()