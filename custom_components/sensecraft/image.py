import logging
import os
from homeassistant import config_entries
from homeassistant.util import dt as dt_util
from homeassistant.core import HomeAssistant
from homeassistant.components.image import ImageEntity
from homeassistant.helpers.device_registry import (
    DeviceInfo,
)
from .core.watcher_local import WatcherLocal
from .const import (
    DOMAIN,
    WATCHER,
    WATCHER_LOCAL,
    DATA_SOURCE
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

    if data_source == WATCHER:
        watcherLocal: WatcherLocal = data[WATCHER_LOCAL]
        deviceId = watcherLocal.deviceId
        entities = [WatcherImage(hass, deviceId)]
        async_add_entities(entities, update_before_add=False)


class WatcherImage(ImageEntity):
    def __init__(
        self,
        hass: HomeAssistant,
        eui: str,
    ) -> None:
        """Initialize the camera entity."""
        self.hass = hass
        ImageEntity.__init__(self, hass)
        self._attr_unique_id = ("watcher_image_{eui}").format(
            eui=eui,
        )
        self._eui = eui
        self._event_type = ("{domain}_{id}").format(
            domain=DOMAIN,
            id=self._attr_unique_id
        )
        self._attr_name = "Alarm Image"
        self._attr_image_last_updated = None
        self._event = None
        self._image_data = None

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        self._event = self.hass.bus.async_listen(
            self._event_type, self.handle_event)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        if self._event:
            self._event()
            self._event = None

    def handle_event(self, event):
        image_path = event.data.get('image_path')
        self._attr_image_last_updated = dt_util.utcnow()
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as file:
                self._image_data = file.read()
            image_size = len(self._image_data)
        else:
            self._image_data = None
        self.hass.async_add_job(self.async_write_ha_state)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self._eui)
            },
            name=self._eui,
            manufacturer="Seeed Studio",
            model="Watcher",
            sw_version="1.0",
        )

    def image(self) -> bytes | None:
        """Return bytes of image."""
        return self._image_data
