"""Demo platform that offers a fake Number entity."""
from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from .core.sscma_local import SScmaLocal
from .const import (
    DOMAIN,
    SSCMA_LOCAL,
    DATA_SOURCE,
    SSCMA,
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
    if data_source == SSCMA:
        local: SScmaLocal = data[SSCMA_LOCAL]
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
        local: SScmaLocal = data[SSCMA_LOCAL]
        if local is not None:
            local.device.tscore = value
            self.async_write_ha_state()


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
        local: SScmaLocal = data[SSCMA_LOCAL]
        if local is not None:
            local.device.tiou = value
            self.async_write_ha_state()
