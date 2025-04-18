from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant.const import Platform
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType

# The domain of your component. Should be equal to the name of your component.
from .const import (
    DOMAIN,
    CLOUD,
    CONFIG_DATA,
    DATA_SOURCE,
    GROVE_VISION_AI,
    WATCHER,
    RECAMERA,
)

# from .mqtt_assistant import MQTTAssistant
from .core.cloud import Cloud
from .core.grove_vision_ai import GroveVisionAI
from .core.watcher import Watcher
from .core.recamera import ReCamera

PLATFORMS = [Platform.CAMERA, Platform.SENSOR, Platform.NUMBER,
             Platform.SELECT, Platform.IMAGE, Platform.BUTTON, Platform.SWITCH]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Sensecraft component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    data = dict(entry.data)
    if entry.options:
        data.update(entry.options)
        entry.data = data
    # Forward the setup to the sensor platform.
    data_source = data.get(DATA_SOURCE)
    entry.async_on_unload(entry.add_update_listener(update_listener))
    if data_source == CLOUD:
        cloud = Cloud.from_config(hass, data.get(CONFIG_DATA))
        data[CLOUD] = cloud

    elif data_source == GROVE_VISION_AI:
        groveVisionAI = GroveVisionAI.from_config(hass, data.get(CONFIG_DATA))
        groveVisionAI.setMqtt()
        data[GROVE_VISION_AI] = groveVisionAI

    elif data_source == WATCHER:
        watcher = Watcher.from_config(hass, data.get(CONFIG_DATA))
        data[WATCHER] = watcher

    elif data_source == RECAMERA:
        recameraLocal = ReCamera.from_config(hass, data.get(CONFIG_DATA))
        await recameraLocal.async_setup()
        data[RECAMERA] = recameraLocal

    hass.data[DOMAIN][entry.entry_id] = data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Unload a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    data_source = data.get(DATA_SOURCE)
    if data_source == CLOUD:
        cloud: Cloud = data[CLOUD]
        cloud.stop()
    elif data_source == GROVE_VISION_AI:
        groveVisionAI: GroveVisionAI = data[GROVE_VISION_AI]
        groveVisionAI.stop()
    elif data_source == WATCHER:
        watcher: Watcher = data[WATCHER]
        watcher.cleanup()
    elif data_source == RECAMERA:
        recameraLocal: ReCamera = data[RECAMERA]
        recameraLocal.cleanup()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    data_source = entry.data.get(DATA_SOURCE)
    
    if data_source == RECAMERA:
        device: ReCamera = hass.data[DOMAIN][entry.entry_id][RECAMERA]
        if device:
            # Update device configuration
            device.update_config(entry.data[CONFIG_DATA])
            
    await hass.config_entries.async_reload(entry.entry_id)
