from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant.const import Platform
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType

# The domain of your component. Should be equal to the name of your component.
from .const import (
    DOMAIN,
    CLOUD,
    JETSON,
    CONFIG_DATA,
    DATA_SOURCE,
    GROVE_VISION_AI_V2,
    WATCHER,
    RECAMERA_GIMBAL,
)

# from .mqtt_assistant import MQTTAssistant
from .core.cloud import Cloud
from .core.jetson import Jetson
from .core.grove_vision_ai_v2 import GroveVisionAiV2
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

    elif data_source == JETSON:
        jetson = Jetson.from_config(
            hass, data.get(CONFIG_DATA))
        jetson.setMqtt()
        data[JETSON] = jetson

    elif data_source == GROVE_VISION_AI_V2:
        groveVisionAiV2 = GroveVisionAiV2.from_config(hass, data.get(CONFIG_DATA))
        groveVisionAiV2.setMqtt()
        data[GROVE_VISION_AI_V2] = groveVisionAiV2

    elif data_source == WATCHER:
        watcher = Watcher.from_config(hass, data.get(CONFIG_DATA))
        data[WATCHER] = watcher

    elif data_source == RECAMERA_GIMBAL:
        recameraLocal = ReCamera.from_config(hass, data.get(CONFIG_DATA))
        recameraLocal.setMqtt()
        data[RECAMERA_GIMBAL] = recameraLocal

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
    elif data_source == JETSON:
        jetson: Jetson = data[JETSON]
        jetson.stop()
    elif data_source == GROVE_VISION_AI_V2:
        groveVisionAiV2: GroveVisionAiV2 = data[GROVE_VISION_AI_V2]
        groveVisionAiV2.stop()
    elif data_source == RECAMERA_GIMBAL:
        recameraLocal: ReCamera = data[RECAMERA_GIMBAL]
        recameraLocal.stop()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
