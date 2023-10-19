"""Config flow for sensecraft integration."""
from __future__ import annotations

import logging
import json
from typing import Any, Dict, Optional
import voluptuous as vol
import hashlib
from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from collections import OrderedDict
from homeassistant.data_entry_flow import FlowResult
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
    ACCOUNT_USERNAME,
    ACCOUNT_PASSWORD,
    SELECTED_DEVICE,
    ACCESS_ID,
    ACCESS_KEY,
    ACCOUNT_ENV,
    ORG_ID,
    ENV_URL,
    PORTAL,
    OPENAPI,
) 
from requests import get,post
_LOGGER = logging.getLogger(__name__)


# Note the input displayed to the user will be translated. See the
# translations/<lang>.json file and strings.json. See here for further information:
# https://developers.home-assistant.io/docs/config_entries_config_flow_handler/#translations
# At the time of writing I found the translations created by the scaffold didn't
# quite work as documented and always gave me the "Lokalise key references" string
# (in square brackets), rather than the actual translated value. I did not attempt to
# figure this out or look further into it.

TEXT_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT))
PASSWORD_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
ENV_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=SUPPORTED_ENV,
        mode=SelectSelectorMode.DROPDOWN,
    )
)

async def sensecapAuth(hass: HomeAssistant,user_input: dict[str, Any], env):
    username = user_input[ACCOUNT_USERNAME]
    password = user_input[ACCOUNT_PASSWORD]
    def login(username: str, password: str):
        hash_object = hashlib.md5(password.encode('utf-8'))
        md5_password = hash_object.hexdigest()
        url = ("{portalurl}/user/login?account={account}&password={password}&origin=1").format(
                portalurl=ENV_URL[env][PORTAL],
                account=username,
                password=md5_password
            )
        response = post(url=url)
        resp = json.loads(response.text)
        data = resp.get('data')
        code = resp.get('code')
        if int(code) != 0 or data is None:
            raise ValueError
        return data
    try:
        authData = await hass.async_add_executor_job(login,username,password)
        return authData
    except:
        raise ValueError
    
async def getApikey(hass: HomeAssistant, token: str, env):
    def getFixedAccess(token: str):
        headers = {
            'Authorization': token,
        }
        url = ("{portalurl}/organization/access/getFixedAccess").format(
                portalurl=ENV_URL[env][PORTAL],
            )
        response = get(url, headers=headers)
        resp = json.loads(response.text)
        data = resp.get('data')
        code = resp.get('code')
        if int(code) != 0 or data is None:
            raise ValueError
        return data
    try:
        apikey = await hass.async_add_executor_job(getFixedAccess,token)
        return apikey
    except:
        raise ValueError

         
async def getDeviceList(hass: HomeAssistant,accessid: str, accesskey:str, env):
    def list_devices(username: str, password: str):
        url = ("{openapi}/list_devices").format(
                openapi=ENV_URL[env][OPENAPI],
            )
        response = get(url, auth=(username, password))
        resp = json.loads(response.text)
        data = resp.get('data')
        code = resp.get('code')
        if int(code) != 0 or data is None:
            raise ValueError
        return data
    try:
        response = await hass.async_add_executor_job(list_devices,accessid,accesskey)
        return response
    except:
        raise ValueError

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
        """Confirm the setup."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                env = user_input[ACCOUNT_ENV]
                userdata = await sensecapAuth(self.hass, user_input, env)
                self.data['user'] = userdata
                apikey = await getApikey(self.hass, userdata.get('token'), env)
                accessid = apikey.get(ACCESS_ID)
                accesskey = apikey.get(ACCESS_KEY)
                self.data[ACCESS_ID] = accessid
                self.data[ACCESS_KEY] = accesskey
                self.data[ACCOUNT_ENV] = env
                return await self.async_step_select()
            except NoApiKey:
                errors["base"] = "no_apikey"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "invalid_auth"

        fields: OrderedDict[Any, Any] = OrderedDict()
        fields[vol.Required(ACCOUNT_USERNAME)] = TEXT_SELECTOR
        fields[vol.Required(ACCOUNT_PASSWORD)] = PASSWORD_SELECTOR
        fields[
        vol.Optional(
            ACCOUNT_ENV,
            description={"suggested_value": ENV_CHINA},
        )
        ] = ENV_SELECTOR

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(fields), errors=errors
        )
        
    async def async_step_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle multiple cloud devices found."""
        errors: dict[str, str] = {}

        accessid = self.data[ACCESS_ID]
        accesskey =self.data[ACCESS_KEY]
        env = self.data[ACCOUNT_ENV]
        if user_input is not None:
            selectDevice = user_input[SELECTED_DEVICE]
            return self.async_create_entry(title="device", data={
                        ORG_ID: self.data['user']['org_id'],
                        ACCESS_ID: self.data[ACCESS_ID],
                        ACCESS_KEY: self.data[ACCESS_KEY],
                        SELECTED_DEVICE: selectDevice,
                        ACCOUNT_ENV: env,
                    })

        deviceList = await getDeviceList(self.hass, accessid, accesskey, env)
        all_device = {device.get('device_eui'): f"{device.get('device_eui')} {device.get('device_name')}" for device in deviceList}
        select_schema = vol.Schema({
            vol.Required(SELECTED_DEVICE): cv.multi_select(
                    all_device
                )
        })

        return self.async_show_form(
            step_id="select", data_schema=select_schema, errors=errors
        )
        
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)
        

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options for the custom component."""
        errors: dict[str, str] = {}
        
        accessid = self.config_entry.data[ACCESS_ID]
        accesskey =self.config_entry.data[ACCESS_KEY]
        env = self.config_entry.data[ACCOUNT_ENV]

        selected = self.config_entry.data[SELECTED_DEVICE]
        if user_input is not None:
            return self.async_create_entry(title="device", data={
                SELECTED_DEVICE: user_input[SELECTED_DEVICE],
                })

        deviceList = await getDeviceList(self.hass, accessid, accesskey, env)
        all_device = {device.get('device_eui'): f"{device.get('device_eui')} {device.get('device_name')}" for device in deviceList}
        select_schema = vol.Schema({
            vol.Required(SELECTED_DEVICE,default=list(selected)): cv.multi_select(
                    all_device
                )
        })

        return self.async_show_form(
            step_id="init", data_schema=select_schema, errors=errors
        )
            
class NoApiKey(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid ApiKey."""