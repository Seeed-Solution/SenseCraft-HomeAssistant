from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from .core.sensecraft_local import SenseCraftLocal
from .const import (
    DOMAIN,
    SENSECRAFT_LOCAL,
    DATA_SOURCE,
    SENSECRAFT,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up stream select platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    data_source = data.get(DATA_SOURCE)
    if data_source == SENSECRAFT:
        local: SenseCraftLocal = data[SENSECRAFT_LOCAL]
        jetsonStreamSelect = JetsonStreamSelect(local.deviceMac, local.deviceName, config_entry.entry_id)
        local.on_monitor_stream_list(jetsonStreamSelect.received_stream_list)
        async_add_entities([jetsonStreamSelect], False)



class JetsonStreamSelect(SelectEntity):
    def __init__(self, id: str, name: str, entry_id: str):
        """Initialize the select."""
        self._attr_unique_id = id
        self._entry_id = entry_id
        self._device_name = name
        self._attr_name = 'stream list'
        self._attr_options = []
        self._attr_current_option = None

    def received_stream_list(self, streams):
        self._attr_options = streams
        if self._attr_current_option is None and len(streams) > 0:
            self._attr_current_option = streams[0]
            data = self.hass.data[DOMAIN][self._entry_id]
            local: SenseCraftLocal = data[SENSECRAFT_LOCAL]
            local.updateStream(streams[0])
        self.hass.async_add_job(self.async_write_ha_state)
            

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._attr_unique_id)
            },
            name=self._device_name,
            manufacturer="Seeed Studio",
            model="Jetson",
            sw_version="1.0",
        )

    # @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return True

    @property
    def options(self):
        """Return a set of selectable options."""
        return self._attr_options
    
    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        self._attr_current_option = option
        data = self.hass.data[DOMAIN][self._entry_id]
        local: SenseCraftLocal = data[SENSECRAFT_LOCAL]
        local.updateStream(option)
        self.hass.async_add_job(self.async_write_ha_state)

    def should_poll():
        return True
