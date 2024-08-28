"""Config flow for sensecraft integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import voluptuous as vol
from homeassistant.components import dhcp, zeroconf
from homeassistant import config_entries, exceptions
import homeassistant.helpers.config_validation as cv
from collections import OrderedDict
from homeassistant.data_entry_flow import FlowResult
from .core.sensecraft_cloud import SenseCraftCloud
from .core.sensecraft_local import SenseCraftLocal
from .core.sscma_local import SScmaLocal
from .core.watcher_local import WatcherLocal
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    DOMAIN,
    SUPPORTED_ENV,
    ENV_CHINA,
    SENSECRAFT,
    SSCMA,
    JETSON_NAME,
    GROVE_WE_2_NAME,
    WATCHER,
    SUPPORTED_DEVICE,
    BROKER,
    PORT,
    ACCOUNT_USERNAME,
    ACCOUNT_PASSWORD,
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_TOPIC,
    SELECTED_DEVICE,
    ACCOUNT_ENV,
    DEVICE_NAME,
    DEVICE_HOST,
    DEVICE_PORT,
    DEVICE_MAC,
    DEVICE_ID,
    DEVICE_TYPE,
    SENSECRAFT_CLOUD,
    SENSECRAFT_LOCAL,
    CONFIG_DATA,
    DATA_SOURCE,
    CLOUD,
)

_LOGGER = logging.getLogger(__name__)
SenseCraft_URL = "https://sensecap.seeed.cc/"


TEXT_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT))
PASSWORD_SELECTOR = TextSelector(
    TextSelectorConfig(type=TextSelectorType.PASSWORD))
ENV_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=SUPPORTED_ENV,
        mode=SelectSelectorMode.DROPDOWN,
    )
)
DEVICE_TYPE_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=SUPPORTED_DEVICE,
        mode=SelectSelectorMode.DROPDOWN,
    )
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sensecap."""

    VERSION = 1
    # Pick one of the available connection classes in homeassistant/config_entries.py
    # This tells HA if it should be asking for updates, or it'll be notified of updates
    # automatically. This example uses PUSH, as the dummy hub will notify HA of
    # changes.
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    data: Optional[Dict[str, Any]] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}
        if user_input is not None:
            action = user_input.get('action')
            if action == 'cloud':
                return await self.async_step_cloud()
            elif action == 'local':
                return await self.async_step_local()

        actions = {
            'cloud': 'Add devices using SenseCraft Account (Cloud)',
            'local': 'Add device using host/id/eui (Local Network)',
        }

        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema({
                vol.Required('action', default='cloud'): vol.In(actions),
            }),
            errors=errors,
        )

    async def async_step_cloud(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the cloud."""
        errors: dict[str, str] = {}
        if user_input is None:
            user_input = {}
        else:
            try:
                cloud = SenseCraftCloud(self.hass)
                username = user_input[ACCOUNT_USERNAME]
                password = user_input[ACCOUNT_PASSWORD]
                env = user_input[ACCOUNT_ENV]
                await cloud.senseCraftAuth(username, password, env)
                self.data[SENSECRAFT_CLOUD] = cloud
                return await self.async_step_cloud_filter()
            except NoApiKey:
                errors["base"] = "no_apikey"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "invalid_auth"

        fields: OrderedDict[Any, Any] = OrderedDict()
        fields[vol.Required(ACCOUNT_USERNAME, default=user_input.get(
            ACCOUNT_USERNAME, ''))] = TEXT_SELECTOR
        fields[vol.Required(ACCOUNT_PASSWORD, default=user_input.get(
            ACCOUNT_PASSWORD, ''))] = PASSWORD_SELECTOR
        fields[vol.Optional(ACCOUNT_ENV, default=user_input.get(
            ACCOUNT_ENV, ENV_CHINA))] = ENV_SELECTOR

        return self.async_show_form(
            step_id="cloud", data_schema=vol.Schema(fields), errors=errors, description_placeholders={"sensecraft_url": SenseCraft_URL},
        )

    async def async_step_cloud_filter(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle multiple cloud devices found."""
        errors: dict[str, str] = {}
        cloud: SenseCraftCloud = self.data[SENSECRAFT_CLOUD]
        if user_input is not None:
            selectDevice = user_input[SELECTED_DEVICE]
            cloud.selectedDeviceEuis = selectDevice
            return self.async_create_entry(title="Cloud Device", data={
                CONFIG_DATA: cloud.to_config(),
                DATA_SOURCE: CLOUD
            })

        deviceList = await cloud.getDeviceList()
        all_device = {device.get('device_eui'): f"{device.get('device_eui')} {device.get('device_name')}" for device in deviceList}

        select_schema = vol.Schema({
            vol.Required(SELECTED_DEVICE): cv.multi_select(
                all_device
            )
        })

        return self.async_show_form(
            step_id="cloud_filter", data_schema=select_schema, errors=errors
        )

    async def async_step_local(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the local."""
        errors: dict[str, str] = {}
        if user_input is None:
            user_input = {}
        else:
            device = user_input['device']
            if device == JETSON_NAME:
                return await self.async_step_local_jetson()
            elif device == GROVE_WE_2_NAME:
                return await self.async_step_local_grove_vision_ai()
            elif device == WATCHER:
                return await self.async_step_local_watcher()

        fields: OrderedDict[Any, Any] = OrderedDict()
        fields[vol.Optional('device', default=user_input.get(
            'device', WATCHER))] = DEVICE_TYPE_SELECTOR

        return self.async_show_form(
            step_id="local", data_schema=vol.Schema(fields), errors=errors
        )

    async def async_step_local_jetson(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm the setup."""
        errors: dict[str, str] = {}
        if user_input is None:
            user_input = {}
        else:
            try:
                host = user_input['host']
                name = user_input['name']
                config: dict[str, str] = {}
                config[DEVICE_HOST] = host
                config[DEVICE_NAME] = name
                config[DEVICE_TYPE] = SENSECRAFT
                local = SenseCraftLocal(self.hass, config)
                info = await local.getInfo()
                device_mac = info.get('mac')
                if device_mac is not None:
                    local.deviceMac = device_mac
                    local.mqttBroker = host
                    local.mqttPort = 1884
                    config = local.to_config()
                    await self.async_set_unique_id(device_mac)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title=name, data={
                        CONFIG_DATA: config,
                        DATA_SOURCE: SENSECRAFT
                    })
                else:
                    errors["base"] = "setup_error"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "setup_error"

        fields: OrderedDict[Any, Any] = OrderedDict()
        fields[vol.Required('host', default=user_input.get(
            'host', ''))] = TEXT_SELECTOR
        fields[vol.Required('name', default=user_input.get(
            'name', JETSON_NAME))] = TEXT_SELECTOR

        return self.async_show_form(
            step_id="local_jetson", data_schema=vol.Schema(fields), errors=errors
        )

    async def async_step_local_grove_vision_ai(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm the setup."""
        errors: dict[str, str] = {}
        if user_input is None:
            user_input = {}
        else:
            id = user_input['id']
            name = f"grove_vision_ai_v2_{id}"
            device: dict[str, str] = {}
            device[DEVICE_NAME] = name
            device[DEVICE_ID] = name
            device[MQTT_TOPIC] = f"sscma/v0/{id}"
            device[MQTT_BROKER] = ''
            device[MQTT_PORT] = ''
            device[DEVICE_TYPE] = SSCMA
            self.context['device'] = device
            await self.async_set_unique_id(name)
            self._abort_if_unique_id_configured()
            return await self.async_step_mqtt()

        fields: OrderedDict[Any, Any] = OrderedDict()
        fields[vol.Required('id', default=user_input.get(
            'id', ''))] = TEXT_SELECTOR

        return self.async_show_form(
            step_id="local_grove_vision_ai", data_schema=vol.Schema(fields), errors=errors
        )

    async def async_step_local_watcher(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm the setup."""
        errors: dict[str, str] = {}
        if user_input is None:
            user_input = {}
        else:
            eui = user_input['eui']
            device: dict[str, str] = {}
            device[DEVICE_ID] = eui
            self.context['device'] = device
            await self.async_set_unique_id(eui)
            self._abort_if_unique_id_configured()
            return await self.async_step_watcher_confirm()

        fields: OrderedDict[Any, Any] = OrderedDict()
        fields[vol.Required('eui', default=user_input.get(
            'eui', ''))] = TEXT_SELECTOR

        return self.async_show_form(
            step_id="local_watcher",
            data_schema=vol.Schema(fields),
            errors=errors
        )

    async def async_step_watcher_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """set up mqtt broker and connect device with tcp."""
        errors: dict[str, str] = {}
        device = self.context['device']
        eui = device[DEVICE_ID]
        if user_input is None:
            user_input = {}
        else:
            try:
                local = WatcherLocal(self.hass, device)
                config = local.to_config()
                return self.async_create_entry(title=eui, data={
                    CONFIG_DATA: config,
                    DATA_SOURCE: WATCHER
                })

            except Exception:
                errors["base"] = "setup_error"

        return self.async_show_form(
            step_id="watcher_confirm",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={"name": eui}
        )

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle zeroconf discovery."""
        print('zeroconf', discovery_info)
        type = discovery_info.type
        name = discovery_info.name
        device_name = name.removesuffix("." + type)
        properties = discovery_info.properties
        device: dict[str, str] = {}
        if type == '_sensecraft._tcp.local.':
            device_mac: str | None = properties.get("mac")
            device_host: str | None = properties.get("host")
            device_port: str | None = properties.get("port")
            mqtt_port: str | None = properties.get("mqtt_port")
            if device_mac is None:
                return self.async_abort(reason="mdns_missing_mac")
            if device_host is None:
                return self.async_abort(reason="mdns_missing_host")
            if device_port is None:
                return self.async_abort(reason="mdns_missing_port")
            if mqtt_port is None:
                return self.async_abort(reason="mdns_missing_mqtt")
            device[DEVICE_NAME] = device_name
            device[DEVICE_HOST] = device_host
            device[DEVICE_PORT] = device_port
            device[DEVICE_MAC] = device_mac
            device[DEVICE_TYPE] = SENSECRAFT
            device[MQTT_BROKER] = device_host
            device[MQTT_PORT] = mqtt_port
            await self.async_set_unique_id(device_mac)
            self._abort_if_unique_id_configured()
            self.context.update(
                {'title_placeholders': {'name': device_name + '_' + device_host}})
            self.context['device'] = device
            return await self.async_step_zeroconf_confirm()

        elif type == '_sscma._tcp.local.':
            mqtt_broker: str | None = properties.get("server")
            mqtt_port: str | None = properties.get("port")
            dest: str | None = properties.get("dest")
            auth: str | None = properties.get("auth")
            if mqtt_broker is None or mqtt_port is None or dest is None:
                return self.async_abort(reason="mdns_missing_mqtt")
            device[DEVICE_NAME] = device_name
            device[DEVICE_ID] = device_name
            device[DEVICE_TYPE] = SSCMA
            device[MQTT_BROKER] = mqtt_broker
            device[MQTT_PORT] = mqtt_port
            device[MQTT_TOPIC] = dest
            await self.async_set_unique_id(device_name)
            self._abort_if_unique_id_configured()
            self.context.update({'title_placeholders': {'name': device_name}})
            self.context['device'] = device
            if auth is not None and auth == 'y':
                return await self.async_step_mqtt()
            else:
                return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by zeroconf."""
        errors: dict[str, str] = {}
        device = self.context['device']
        device_name = device[DEVICE_NAME]
        device_type = device[DEVICE_TYPE]
        if user_input is not None:
            if device_type == SENSECRAFT:
                local = SenseCraftLocal(self.hass, device)
            elif device_type == SSCMA:
                local = SScmaLocal(self.hass, device)
            config = local.to_config()
            return self.async_create_entry(title=device_name, data={
                CONFIG_DATA: config,
                DATA_SOURCE: device_type
            })

        return self.async_show_form(
            step_id="zeroconf_confirm",
            errors=errors,
            description_placeholders={"name": device_name},
        )

    async def async_step_mqtt(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """set up mqtt broker and connect device with tcp."""
        errors: dict[str, str] = {}
        device = self.context['device']
        device_name = device[DEVICE_NAME]
        device_type = device[DEVICE_TYPE]
        mqtt_broker = device[MQTT_BROKER]
        mqtt_port = device[MQTT_PORT]
        if user_input is None:
            user_input = {}
        else:
            try:
                local = SScmaLocal(self.hass, device)
                local.mqttBroker = user_input[BROKER]
                local.mqttPort = user_input[PORT]
                local.mqttUsername = user_input[ACCOUNT_USERNAME]
                local.mqttPassword = user_input[ACCOUNT_PASSWORD]

                if local.setMqtt():
                    local.stop()
                    config = local.to_config()
                    return self.async_create_entry(title=device_name, data={
                        CONFIG_DATA: config,
                        DATA_SOURCE: device_type
                    })
                else:
                    errors["base"] = "setup_error"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "setup_error"
        fields: OrderedDict[Any, Any] = OrderedDict()
        fields[vol.Required(BROKER, default=user_input.get(
            BROKER, mqtt_broker))] = TEXT_SELECTOR
        fields[vol.Required(PORT, default=user_input.get(
            PORT, mqtt_port))] = TEXT_SELECTOR
        fields[vol.Optional(ACCOUNT_USERNAME, default=user_input.get(
            ACCOUNT_USERNAME, ''))] = TEXT_SELECTOR
        fields[vol.Optional(ACCOUNT_PASSWORD, default=user_input.get(
            ACCOUNT_PASSWORD, ''))] = PASSWORD_SELECTOR

        return self.async_show_form(
            step_id="mqtt",
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders={"name": device_name}
        )


class NoApiKey(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid ApiKey."""
