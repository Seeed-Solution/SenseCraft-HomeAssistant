"""Button platform for Sensecraft."""
import logging
from homeassistant.components.button import ButtonEntity
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

_LOGGER = logging.getLogger(__name__)

BUTTON_TYPES = {
    "sleep": {
        "name": "Sleep",
        "icon": "mdi:power-sleep",
        "command": {"command": "sleep"}
    },
    "standby": {
        "name": "Standby",
        "icon": "mdi:power-standby",
        "command": {"command": "standby"}
    },
    "calibrate": {
        "name": "Calibrate",
        "icon": "mdi:adjust",
        "command": {"command": "calibrate"}
    },
    "emergency_stop": {
        "name": "Emergency Stop",
        "icon": "mdi:stop",
        "command": {"command": "emergency_stop"}
    },
}

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    data_source = data.get(DATA_SOURCE)
    
    if data_source == RECAMERA:
        recamera: ReCamera = data[RECAMERA]
        entities = []
        
        # 为每种按钮类型创建实体
        for button_type, button_info in BUTTON_TYPES.items():
            entities.append(
                ReCameraButton(
                    recamera,
                    button_type,
                    button_info
                )
            )
        
        async_add_entities(entities)

class ReCameraButton(ButtonEntity):
    """Representation of a ReCamera button."""

    def __init__(self, recamera: ReCamera, button_type: str, button_info: dict):
        """Initialize the button entity."""
        self._recamera = recamera
        self._button_type = button_type
        self._attr_name = f"{recamera.deviceName} {button_info["name"]}"
        self._attr_unique_id = f"{recamera.deviceId}_{button_type}"
        self._attr_icon = button_info["icon"]
        self._command = button_info["command"]
        self._event = None
        
        # 设置设备信息
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

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self._event = self.hass.bus.async_listen(
            f"sensecraft_recamera_{self._recamera.deviceId}_connection_state",
            self._handle_connection_state
        )

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        if self._event:
            self._event()
            self._event = None

    def _handle_connection_state(self, event):
        """Handle connection state changes."""
        self._recamera.connected = event.data.get("connected", False)
        self.hass.loop.call_soon_threadsafe(self.async_schedule_update_ha_state)

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            # 使用 ReCamera 的 send_control 方法发送命令
            result = await self._recamera.send_control(self._command)
            if result:
                _LOGGER.info(f"Command {self._button_type} sent successfully to {self._recamera.deviceId}")
        except Exception as e:
            _LOGGER.error(f"Error sending {self._button_type} command: {e}") 