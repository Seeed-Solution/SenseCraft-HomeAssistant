from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant.helpers import device_registry
from homeassistant.const import Platform

# The domain of your component. Should be equal to the name of your component.
from .const import (
    DOMAIN
)

PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(
    hass: HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    data = dict(entry.data)
    if entry.options:
        data.update(entry.options)
        entry.data=data
    hass.data[DOMAIN][entry.entry_id] = data
    # # Forward the setup to the sensor platform.
    entry.async_on_unload(entry.add_update_listener(update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(
    hass: HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def update_listener(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

# async def async_remove_config_entry_device(
#     hass: HomeAssistant, entry: config_entries.ConfigEntry, device_entry: device_registry.DeviceEntry
# ) -> bool:
#     """Remove device from a config entry."""
#     eui = list(device_entry.identifiers)[0][1]
#     if entry.options:
#         options = dict(entry.options)
#         selected_device_options = options[SELECTED_DEVICE]
#         selected_device_options.pop(eui)
#         options[SELECTED_DEVICE] = selected_device_options
#         entry.options = options

#     data = dict(entry.data)
#     selected_device = data[SELECTED_DEVICE]
#     selected_device.pop(eui)
#     data[SELECTED_DEVICE] = selected_device
#     entry.data = data
    
#     return True
