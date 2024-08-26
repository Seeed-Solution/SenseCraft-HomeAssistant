from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from base64 import b64decode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from .core.sensecraft_local import SenseCraftLocal
from .core.sscma_local import SScmaLocal
from .const import (
    DOMAIN,
    SENSECRAFT_LOCAL,
    SSCMA_LOCAL,
    DATA_SOURCE,
    SENSECRAFT,
    SSCMA,
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][config_entry.entry_id]
    data_source = data.get(DATA_SOURCE)
    if data_source == SENSECRAFT:
        senseCraftLocal: SenseCraftLocal = data[SENSECRAFT_LOCAL]
        camera = JetsonCamera(senseCraftLocal.deviceMac, senseCraftLocal.deviceName)
        senseCraftLocal.on_monitor_stream(camera.received_image)
        async_add_entities([camera], False)
    elif data_source == SSCMA:
        sscmaLocal: SScmaLocal = data[SSCMA_LOCAL]
        camera = SSCMACamera(sscmaLocal.deviceId, sscmaLocal.deviceName)
        sscmaLocal.on_monitor_stream(camera.received_image)
        async_add_entities([camera], False)


class CameraBase(Camera):
    """Representation of an camera entity."""

    def __init__(
        self,
        id: str, 
        name:str,
    ) -> None:
        """Initialize the camera entity."""
        super().__init__()
        self._attr_frame_interval = 0.1
        self._attr_name = name
        self._device_name = name
        self._attr_unique_id = id
        self._stream_source = None
        self._attr_is_streaming = True


    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes:
        """Return a faked still image response."""
        return self._stream_source

    def received_image(self, frame):
        self._stream_source = b64decode(frame)
    
    def should_poll():
        return True

class JetsonCamera(CameraBase):

    def __init__(
        self,
        mac: str, 
        name:str,
    ) -> None:
        """Initialize the image entity."""
        super().__init__(mac, name)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self._attr_unique_id)
            },
            name=self._device_name,
            manufacturer="Seeed Studio",
            model="Jetson",
            sw_version="1.0",
        )

class SSCMACamera(CameraBase):

    def __init__(
        self,
        id: str, 
        name:str,
    ) -> None:
        """Initialize the image entity."""
        super().__init__(id, name)
        number = name.split("_")[-1]
        self._model = name.removesuffix("_" + number)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self._attr_unique_id)
            },
            name=self._device_name,
            manufacturer="Seeed Studio",
            model=self._model,
            sw_version="1.0",
        )
