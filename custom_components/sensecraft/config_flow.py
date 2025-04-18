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
from .core.cloud import Cloud
from .core.grove_vision_ai import GroveVisionAI
from .core.recamera import ReCamera
from .core.watcher import Watcher
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.core import callback

from .const import (
    DOMAIN,
    SUPPORTED_ENV,
    ENV_CHINA,
    GROVE_VISION_AI,
    WATCHER,
    RECAMERA,
    SUPPORTED_DEVICE,
    BROKER,
    PORT,
    CLIENT_ID,
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
    CLOUD,
    CONFIG_DATA,
    DATA_SOURCE,
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

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        # Only return OptionsFlowHandler for ReCamera devices
        if config_entry.data.get(DATA_SOURCE) == RECAMERA:
            return OptionsFlowHandler(config_entry)
        # Return a dummy options flow for non-ReCamera devices
        return DummyOptionsFlowHandler(config_entry)

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
                cloud = Cloud(self.hass)
                username = user_input[ACCOUNT_USERNAME]
                password = user_input[ACCOUNT_PASSWORD]
                env = user_input[ACCOUNT_ENV]
                await cloud.senseCraftAuth(username, password, env)
                self.data[CLOUD] = cloud
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
        cloud: Cloud = self.data[CLOUD]
        if user_input is not None:
            selectDevice = user_input[SELECTED_DEVICE]
            cloud.selectedDeviceEuis = selectDevice
            return self.async_create_entry(title="Cloud Device", data={
                CONFIG_DATA: cloud.to_config(),
                DATA_SOURCE: CLOUD
            })

        deviceList = await cloud.getDeviceList()
        all_device = {device.get(
            'device_eui'): f"{device.get('device_eui')} {device.get('device_name')}" for device in deviceList}

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
            if device == GROVE_VISION_AI:
                return await self.async_step_local_grove_vision_ai()
            elif device == WATCHER:
                return await self.async_step_local_watcher()
            elif device == RECAMERA:
                return await self.async_step_local_recamera()
        fields: OrderedDict[Any, Any] = OrderedDict()
        fields[vol.Optional('device', default=user_input.get(
            'device', GROVE_VISION_AI))] = DEVICE_TYPE_SELECTOR

        return self.async_show_form(
            step_id="local", data_schema=vol.Schema(fields), errors=errors
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
            device[DEVICE_ID] = id
            device[MQTT_BROKER] = ''
            device[MQTT_PORT] = ''
            device[CLIENT_ID] = name
            device[DEVICE_TYPE] = GROVE_VISION_AI
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
        mqtt_topic = device.get(MQTT_TOPIC)
        has_mqtt_topic = bool(mqtt_topic)
        client_id = device.get(CLIENT_ID)

        if user_input is None:
            user_input = {}
        else:
            try:
                client_id = user_input[CLIENT_ID]
                if not has_mqtt_topic:
                    device[MQTT_TOPIC] = f"sscma/v0/{client_id}"
                local = GroveVisionAI(self.hass, device)
                local.mqttBroker = user_input[BROKER]
                local.mqttPort = user_input[PORT]
                if not has_mqtt_topic:
                    local.clientId = client_id
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
                    errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "setup_error"
        fields: OrderedDict[Any, Any] = OrderedDict()
        fields[vol.Required(BROKER, default=user_input.get(
            BROKER, mqtt_broker))] = TEXT_SELECTOR
        fields[vol.Required(PORT, default=user_input.get(
            PORT, mqtt_port))] = TEXT_SELECTOR
        if not has_mqtt_topic:
            fields[vol.Required(CLIENT_ID, default=user_input.get(
                CLIENT_ID, client_id))] = TEXT_SELECTOR
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

    async def async_step_local_recamera(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm the setup."""
        errors: dict[str, str] = {}
        if user_input is None:
            user_input = {}
        else:
            sn = user_input['device_id']
            device: dict[str, str] = {}
            device[DEVICE_ID] = sn
            self.context['device'] = device

            # 设置唯一ID并检查是否已配置
            await self.async_set_unique_id(sn)
            self._abort_if_unique_id_configured()
            
            # 直接进入下一步，不进行连接测试
            return await self.async_step_recamera_confirm()

        fields: OrderedDict[Any, Any] = OrderedDict()
        fields[vol.Required('device_id', default=user_input.get(
            'device_id', ''))] = TEXT_SELECTOR

        return self.async_show_form(
            step_id="local_recamera", 
            data_schema=vol.Schema(fields), 
            errors=errors
        )

    async def async_step_recamera_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Set up WebSocket connection and verify device."""
        errors: dict[str, str] = {}
        device = self.context['device']
        sn = device[DEVICE_ID]
        name = f"recamera_gimbal_{sn}"
        
        if user_input is None:
            user_input = {}
        else:
            # 获取用户输入的IP地址
            ip = user_input['device_host']
            device[DEVICE_HOST] = ip
            
            try:
                # 创建临时ReCamera实例并测试连接
                local = ReCamera(self.hass, device)
                if await local.async_test_connection():
                    config = local.to_config()
                    return self.async_create_entry(title=name, data={
                        CONFIG_DATA: config,
                        DATA_SOURCE: RECAMERA
                    })
                else:
                    errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "setup_error"

        # 显示IP输入表单
        fields: OrderedDict[Any, Any] = OrderedDict()
        fields[vol.Required('device_host', default=user_input.get(
            'device_host', ''))] = TEXT_SELECTOR

        return self.async_show_form(
            step_id="recamera_confirm",
            data_schema=vol.Schema(fields),
            errors=errors
        )

    async def async_step_local_watcher(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm the setup."""
        errors: dict[str, str] = {}
        if user_input is None:
            user_input = {}
        else:
            eui = user_input['device_id']
            device: dict[str, str] = {}
            device[DEVICE_ID] = eui
            self.context['device'] = device

            await self.async_set_unique_id(eui)
            self._abort_if_unique_id_configured()
            return await self.async_step_watcher_confirm()

        fields: OrderedDict[Any, Any] = OrderedDict()
        fields[vol.Required('device_id', default=user_input.get(
            'device_id', ''))] = TEXT_SELECTOR

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
        name = f"watcher_{eui}"
        if user_input is None:
            user_input = {}
        else:
            try:
                local = Watcher(self.hass, device)
                config = local.to_config()
                return self.async_create_entry(title=name, data={
                    CONFIG_DATA: config,
                    DATA_SOURCE: WATCHER
                })

            except Exception:
                errors["base"] = "setup_error"

        return self.async_show_form(
            step_id="watcher_confirm",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={"name": name}
        )

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle zeroconf discovery."""
        type = discovery_info.type
        name = discovery_info.name
        device_name = name.removesuffix("." + type)
        properties = discovery_info.properties
        device: dict[str, str] = {}
        if type == '_sscma._tcp.local.':
            mqtt_broker: str | None = properties.get("server")
            mqtt_port: str | None = properties.get("port")
            dest: str | None = properties.get("dest")
            auth: str | None = properties.get("auth")
            if mqtt_broker is None or mqtt_port is None or dest is None:
                return self.async_abort(reason="mdns_missing_mqtt")
            device[DEVICE_NAME] = device_name
            device[DEVICE_ID] = device_name
            device[DEVICE_TYPE] = GROVE_VISION_AI
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
            if device_type == GROVE_VISION_AI:
                local = GroveVisionAI(self.hass, device)
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


class DummyOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for non-ReCamera devices."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        # For non-ReCamera devices, show a message that no configuration is needed
        if user_input is not None:
            return self.async_create_entry(title="", data=self.config_entry.options)

        # Get the device type
        device_type = self.config_entry.data.get(DATA_SOURCE, "Unknown")

        # Create a schema with a description
        schema = vol.Schema({})

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={
                "device_name": self.config_entry.title,
                "message": f"No configuration options are available for {device_type} devices."
            }
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        # Only handle ReCamera devices
        if self.config_entry.data.get(DATA_SOURCE) != RECAMERA:
            return self.async_abort(reason="not_recamera")

        if user_input is not None:
            # Create a new config with updated values
            new_config = dict(self.config_entry.data[CONFIG_DATA])
            new_config[DEVICE_HOST] = user_input[DEVICE_HOST]

            # Update the config entry with new values
            return self.async_create_entry(
                title="",
                data={
                    CONFIG_DATA: new_config,
                    DATA_SOURCE: RECAMERA
                }
            )

        # Get current values
        current_config = self.config_entry.data.get(CONFIG_DATA, {})

        # Create schema with current values, only IP is editable
        schema = vol.Schema({
            vol.Required(
                DEVICE_HOST,
                default=current_config.get(DEVICE_HOST, "")
            ): str,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={
                "device_name": self.config_entry.title,
                "message": "You can update the IP address of your ReCamera device."
            }
        )


class NoApiKey(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid ApiKey."""
