"""Demo platform that offers a fake Number entity."""
from __future__ import annotations
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from .core.grove_vision_ai import GroveVisionAI
from .core.recamera import ReCamera
from .const import (
    DOMAIN,
    DATA_SOURCE,
    GROVE_VISION_AI,
    RECAMERA,
)
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    data_source = data.get(DATA_SOURCE)
    if data_source == GROVE_VISION_AI:
        local: GroveVisionAI = data[GROVE_VISION_AI]
        async_add_entities(
            [
                Confidence(
                    local.deviceId,
                    local.deviceName,
                    config_entry.entry_id,
                    local.device.tscore,
                ),
                IOU(
                    local.deviceId,
                    local.deviceName,
                    config_entry.entry_id,
                    local.device.tiou,
                ),
            ]
        )
    elif data_source == RECAMERA:
        recamera: ReCamera = data[RECAMERA]
        motors = [
            ReCameraMotor(recamera, "Yaw Motor", 0x141, 0, 360),
            ReCameraMotor(recamera, "Pitch Motor", 0x142, 0, 180),
        ]
        async_add_entities(motors, False)


class ConfigNumber(NumberEntity):
    """Representation of Config Number entity."""

    def __init__(
        self,
        id: str,
        name: str,
        entry_id: str,
        state: float,
    ) -> None:
        """Initialize the Config Number entity."""
        self._id = id
        self._device_name = name
        self._attr_mode = NumberMode.AUTO
        self._attr_native_unit_of_measurement = "%"
        self._attr_native_value = state
        self._entry_id = entry_id
        self._attr_native_min_value = 1
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        number = name.split("_")[-1]
        self._model = name.removesuffix("_" + number)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._id)
            },
            name=self._device_name,
            manufacturer="Seeed Studio",
            model=self._model,
            sw_version="1.0",
        )

    def should_poll():
        return True


class Confidence(ConfigNumber):
    """Representation of Confidence entity."""

    def __init__(
        self,
        id: str,
        name: str,
        entry_id: str,
        state: float | None,
    ) -> None:
        """Initialize the Confidence entity."""
        # 如果 state 为 None，使用默认值 70
        default_value = 70.0
        super().__init__(id, name, entry_id, state if state is not None else default_value)
        self._attr_unique_id = id + "_" + "confidence"
        self._attr_icon = "mdi:filter-outline"
        self._attr_name = "Confidence"

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._attr_native_value = value
        data = self.hass.data[DOMAIN][self._entry_id]
        local: GroveVisionAI = data[GROVE_VISION_AI]
        if local is not None:
            local.device.tscore = value
            self.async_schedule_update_ha_state()


class IOU(ConfigNumber):
    """Representation of IOU entity."""

    def __init__(
        self,
        id: str,
        name: str,
        entry_id: str,
        state: float | None,
    ) -> None:
        """Initialize the IOU entity."""
        # 如果 state 为 None，使用默认值 70
        default_value = 70.0
        super().__init__(id, name, entry_id, state if state is not None else default_value)
        self._attr_unique_id = id + "_" + "iou"
        self._attr_icon = "mdi:vector-intersection"
        self._attr_name = "IOU"

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._attr_native_value = value
        data = self.hass.data[DOMAIN][self._entry_id]
        local: GroveVisionAI = data[GROVE_VISION_AI]
        if local is not None:
            local.device.tiou = value
            self.async_schedule_update_ha_state()


class ReCameraMotor(NumberEntity):
    """Representation of a ReCamera motor control."""

    def __init__(
        self,
        recamera: ReCamera,
        name: str,
        motor_id: int,
        min_value: float,
        max_value: float,
    ) -> None:
        """Initialize the motor control."""
        self._recamera = recamera
        self._attr_name = f"{recamera.deviceName} {name}"
        self._attr_unique_id = f"{recamera.deviceId}_{motor_id}"
        self._event_type = f"sensecraft_recamera_{self._attr_unique_id}_angle"
        self._event = None
        self._connection_event = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, recamera.deviceId)},
            name=recamera.deviceName,
            manufacturer="Seeed Studio",
            model="ReCamera",
            sw_version="1.0",
        )
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = 1.0
        self._attr_native_value = 0.0
        self._attr_mode = NumberMode.SLIDER
        self.motor_id = motor_id

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
            motor_id = state_data.get("motor_id")
            angle = state_data.get("angle")
            if motor_id == self.motor_id:
                self.update_state(angle)
        except Exception as e:
            _LOGGER.error("Error handling state event: %s", e)

    async def async_set_native_value(self, value: float) -> None:
        """Set the motor position."""
        try:
            # 构建控制命令
            command = {
                "command": "set_angle",
                'param': {
                    "motor_id": self.motor_id,
                    "angle": value
                }
            }
            # 发送控制命令
            result = await self._recamera.send_control(command)
            if result and result.get('code') == 0:
                self._attr_native_value = value
                self.async_schedule_update_ha_state()
            
        except Exception as e:
            _LOGGER.error("Error setting motor position: %s", e)

    def update_state(self, angle: float) -> None:
        """更新电机状态."""
        self._attr_native_value = angle
        self.hass.loop.call_soon_threadsafe(self.async_schedule_update_ha_state)

