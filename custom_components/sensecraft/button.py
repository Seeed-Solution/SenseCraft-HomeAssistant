"""Button platform for Sensecraft."""
import json
import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DOMAIN,
    DATA_SOURCE,
    RECAMERA_GIMBAL,
)

_LOGGER = logging.getLogger(__name__)

BUTTON_TYPES = {
    "sleep": {
        "name": "Sleep",
        "icon": "mdi:power-sleep",
        "command": {"code": 0, "data": {"type": "motor_control", "command": "sleep"}}
    },
    "standby": {
        "name": "Standby",
        "icon": "mdi:power-standby",
        "command": {"code": 0, "data": {"type": "motor_control", "command": "standby"}}
    },
    "calibrate": {
        "name": "Calibrate",
        "icon": "mdi:adjust",
        "command": {"code": 0, "data": {"type": "motor_control", "command": "calibrate"}}
    },
    "emergency_stop": {
        "name": "Emergency Stop",
        "icon": "mdi:stop",
        "command": {"code": 0, "data": {"type": "motor_control", "command": "emergency_stop"}}
    }
}

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    data_source = data.get(DATA_SOURCE)
    
    if data_source == RECAMERA_GIMBAL:
        recamera = data[RECAMERA_GIMBAL]
        entities = []
        
        # 为每种按钮类型创建实体
        for button_type, button_info in BUTTON_TYPES.items():
            entities.append(
                ReCameraButton(
                    recamera,
                    button_type,
                    button_info["name"],
                    button_info["icon"],
                    button_info["command"]
                )
            )
        
        async_add_entities(entities)

class ReCameraButton(ButtonEntity):
    """Representation of a ReCamera button."""

    def __init__(self, recamera, button_type, name, icon, command):
        """Initialize the button entity."""
        self._recamera = recamera
        self._button_type = button_type
        self._attr_name = f"{recamera.deviceName} {name}"
        self._attr_unique_id = f"{recamera.deviceId}_{button_type}"
        self._attr_icon = icon
        self._command = command
        
        # 设置设备信息
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, recamera.deviceId)},
            name=recamera.deviceName,
            manufacturer="Seeed Studio",
            model="ReCamera",
            sw_version="1.0",
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            # 发送控制命令
            self._recamera.send_control(self._command)
            _LOGGER.info(f"Sent command {self._button_type} to {self._recamera.deviceId}")
        except Exception as e:
            _LOGGER.error(f"Error sending {self._button_type} command: {e}") 