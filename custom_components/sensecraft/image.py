import logging
import os
from homeassistant import config_entries
from homeassistant.util import dt as dt_util
from homeassistant.core import HomeAssistant
from homeassistant.components.image import ImageEntity
from homeassistant.helpers.device_registry import (
    DeviceInfo,
)
from .core.watcher import Watcher
from .const import (
    DOMAIN,
    WATCHER,
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
        watcher: Watcher = data[WATCHER]
        deviceId = watcher.deviceId
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
        self._attr_unique_id = f"watcher_image_{eui}"
        self._eui = eui
        self._event_type = f"{DOMAIN}_{self._attr_unique_id}"
        self._attr_name = "Alarm Triggered"
        self._attr_image_last_updated = None
        self._event = None
        self._image_path = None

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
        alarm_text = event.data.get('alarm_text')
        if image_path and os.path.exists(image_path):
            self._image_path = image_path
            image_url = f"http://<home-assistant-url>/local/images/{os.path.basename(image_path)}"
            self.hass.bus.fire('logbook_entry', {
                'name': self._attr_name,
                'message': f'"{alarm_text}"  View image: {image_url}',
                'entity_id': self.entity_id
            })
        else:
            self._image_path = None

        self._attr_image_last_updated = dt_util.utcnow() 
        if self.hass:
            self.hass.loop.call_soon_threadsafe(self.async_schedule_update_ha_state)

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
        if self._image_path and os.path.exists(self._image_path):
            with open(self._image_path, 'rb') as file:
                return file.read()
        return None
    