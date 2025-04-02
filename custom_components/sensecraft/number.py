"""Demo platform that offers a fake Number entity."""
from __future__ import annotations
import json  # 添加 json 导入

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from .core.grove_vision_ai_v2 import GroveVisionAiV2
from .core.recamera import ReCamera
from .const import (
    DOMAIN,
    DATA_SOURCE,
    GROVE_VISION_AI_V2,
    RECAMERA_GIMBAL,
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
    if data_source == GROVE_VISION_AI_V2:
        local: GroveVisionAiV2 = data[GROVE_VISION_AI_V2]
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
    elif data_source == RECAMERA_GIMBAL:
        recamera: ReCamera = data[RECAMERA_GIMBAL]
        motors = [
            ReCameraMotor(recamera, "Yaw Motor", 0x141, 0, 360),
            ReCameraMotor(recamera, "Pitch Motor", 0x142, 0, 180),
        ]
        # 设置状态更新回调
        recamera.on_received_state(lambda msg: handle_motor_state(motors, msg))
        async_add_entities(motors, False)

        # jetson: Jetson = data[JETSON]
        # camera = JetsonCamera(jetson.deviceMac, jetson.deviceName)
        # jetson.on_monitor_stream(camera.received_image)
        # async_add_entities([camera], False)

def handle_motor_state(motors, msg):
    """处理电机状态更新."""
    try:
        if isinstance(msg, bytes):
            state_data = json.loads(msg.decode())
        else:
            state_data = json.loads(msg)

        if state_data.get("state") == "set_angle":
            motor_id = state_data.get("motor_id")
            angle = state_data.get("angle")
            
            for motor in motors:
                if motor.motor_id == motor_id:
                    motor.update_state(angle)
                    break
    except Exception as e:
        _LOGGER.error("Error handling motor state: %s", e)

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
        state: float,
    ) -> None:
        """Initialize the Confidence entity."""
        super().__init__(id, name, entry_id, state)
        self._attr_unique_id = id + "_" + "confidence"
        self._attr_icon = "mdi:filter-outline"
        self._attr_name = "Confidence"

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._attr_native_value = value
        data = self.hass.data[DOMAIN][self._entry_id]
        local: GroveVisionAiV2 = data[GROVE_VISION_AI_V2]
        if local is not None:
            local.device.tscore = value
            if self.hass:
                self.hass.loop.call_soon_threadsafe(self.async_schedule_update_ha_state)


class IOU(ConfigNumber):
    """Representation of IOU entity."""

    def __init__(
        self,
        id: str,
        name: str,
        entry_id: str,
        state: float,
    ) -> None:
        """Initialize the IOU entity."""
        super().__init__(id, name, entry_id, state)
        self._attr_unique_id = id + "_" + "iou"
        self._attr_icon = "mdi:vector-intersection"
        self._attr_name = "IOU"

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._attr_native_value = value
        data = self.hass.data[DOMAIN][self._entry_id]
        local: GroveVisionAiV2 = data[GROVE_VISION_AI_V2]
        if local is not None:
            local.device.tiou = value
            if self.hass:
                self.hass.loop.call_soon_threadsafe(self.async_schedule_update_ha_state)


class ReCameraMotor(NumberEntity):
    """Representation of a ReCamera motor control."""

    def __init__(
        self,
        recamera,
        name: str,
        motor_id: int,
        min_value: float,
        max_value: float,
    ) -> None:
        """Initialize the motor control."""
        self._recamera = recamera
        self._attr_name = f"{recamera.deviceName} {name}"
        self._attr_unique_id = f"{recamera.deviceId}_{motor_id}"
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
        # self.hass = recamera.hass

    async def async_set_native_value(self, value: float) -> None:
        """Set the motor position."""
        try:
            # 构建控制命令
            command = {
                "code": 0,
                "data": {
                    "type": "motor_control",
                    "command": "set_angle",
                    "motor_id": self.motor_id,
                    "angle": value
                }
            }
            # 发送控制命令
            self._recamera.send_control(command)
            self._attr_native_value = value
            if self.hass:
                self.hass.loop.call_soon_threadsafe(self.async_schedule_update_ha_state)
        except Exception as e:
            _LOGGER.error("Error setting motor position: %s", e)

    def update_state(self, angle: float) -> None:
        """更新电机状态."""
        self._attr_native_value = angle
        if self.hass:
            self.hass.loop.call_soon_threadsafe(self.async_schedule_update_ha_state)
