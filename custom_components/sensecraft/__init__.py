from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant.const import Platform

# The domain of your component. Should be equal to the name of your component.
from .const import (
    DOMAIN,
    SENSECRAFT_CLOUD,
    SENSECRAFT_LOCAL,
    SSCMA_LOCAL,
    WATCHER_LOCAL,
    CONFIG_DATA,
    DATA_SOURCE,
    CLOUD,
    SENSECRAFT,
    SSCMA,
    WATCHER
)

# from .mqtt_assistant import MQTTAssistant
from .core.sensecraft_cloud import SenseCraftCloud
from .core.sensecraft_local import SenseCraftLocal
from .core.sscma_local import SScmaLocal
from .core.watcher_local import WatcherLocal

PLATFORMS = [Platform.CAMERA, Platform.SENSOR, Platform.NUMBER,
             Platform.SELECT, Platform.IMAGE]


async def async_setup_entry(
    hass: HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    data = dict(entry.data)
    if entry.options:
        data.update(entry.options)
        entry.data = data
    # # Forward the setup to the sensor platform.
    data_source = data.get(DATA_SOURCE)
    entry.async_on_unload(entry.add_update_listener(update_listener))
    if data_source == CLOUD:
        cloud = SenseCraftCloud.from_config(hass, data.get(CONFIG_DATA))
        data[SENSECRAFT_CLOUD] = cloud

    elif data_source == SENSECRAFT:
        senseCraftLocal = SenseCraftLocal.from_config(
            hass, data.get(CONFIG_DATA))
        senseCraftLocal.setMqtt()
        data[SENSECRAFT_LOCAL] = senseCraftLocal

    elif data_source == SSCMA:
        sscmaLocal = SScmaLocal.from_config(hass, data.get(CONFIG_DATA))
        sscmaLocal.setMqtt()
        data[SSCMA_LOCAL] = sscmaLocal

    elif data_source == WATCHER:
        watcherLocal = WatcherLocal.from_config(hass, data.get(CONFIG_DATA))
        watcherLocal.setMqtt()
        data[WATCHER_LOCAL] = watcherLocal

    hass.data[DOMAIN][entry.entry_id] = data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    data_source = data.get(DATA_SOURCE)
    if data_source == CLOUD:
        cloud: SenseCraftCloud = data[SENSECRAFT_CLOUD]
        cloud.stop()
    elif data_source == SENSECRAFT:
        senseCraftLocal: SenseCraftLocal = data[SENSECRAFT_LOCAL]
        senseCraftLocal.stop()
    elif data_source == SSCMA:
        sscmaLocal: SScmaLocal = data[SSCMA_LOCAL]
        sscmaLocal.stop()
    elif data_source == WATCHER:
        watcherLocal: WatcherLocal = data[WATCHER_LOCAL]
        watcherLocal.stop()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
