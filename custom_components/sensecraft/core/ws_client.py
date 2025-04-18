"""WebSocket client for Sensecraft."""
import json
import logging
import asyncio
from aiohttp import WSMsgType
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)


class WSClient:
    """WebSocket client for a single device connection."""

    def __init__(self, hass: HomeAssistant, device_id: str, device_host: str):
        """Initialize the WebSocket client for a specific device."""
        self.hass = hass
        self.device_id = device_id
        self.device_host = device_host
        self._ws_url = f"ws://{self.device_host}:8090" if self.device_host else None
        self._client = None
        self._task = None
        self._message_callback = None
        self._state_callback = None

    @property
    def is_connected(self) -> bool:
        """Check if the WebSocket connection is active."""
        return self._client is not None and not self._client.closed

    async def async_connect(self) -> bool:
        """Establish WebSocket connection to the device.
        
        Returns:
            bool: True if connection successful, False otherwise.
        """
        if self.is_connected:
            _LOGGER.warning("WebSocket connection already exists for device %s", self.device_id)
            return False

        if not self._ws_url:
            _LOGGER.error("Cannot connect: WebSocket URL is not available for device %s", self.device_id)
            return False

        try:
            # Ensure cleanup of any existing connection
            if self._client:
                await self.async_disconnect()
                
            session = async_get_clientsession(self.hass)
            self._client = await session.ws_connect(
                self._ws_url, 
                heartbeat=30,  # Send heartbeat every 30 seconds
                timeout=10,    # Connection timeout of 10 seconds
                receive_timeout=30,  # Message receive timeout of 30 seconds
                autoclose=True,  # Automatically close connection on errors
                autoping=True    # Automatically send ping messages
            )
            _LOGGER.info("WebSocket connected to %s for device %s", self._ws_url, self.device_id)

            # Create message receiving task
            self._task = self.hass.async_create_task(self._receive_messages())

            if self._state_callback:
                self._state_callback(True)
            return True
        except Exception as e:
            _LOGGER.error("Failed to connect to WebSocket for device %s: %s", self.device_id, e)
            if self._state_callback:
                self._state_callback(False)
            return False

    async def _receive_messages(self):
        """Receive and process WebSocket messages.
        
        Handles different message types:
        - BINARY: Process binary data through callback
        - ERROR/CLOSED/CLOSING: Handle connection termination
        """
        if not self._client:
            return

        try:
            while self.is_connected:
                try:
                    msg = await self._client.receive(timeout=30)
                    
                    if msg.type == WSMsgType.BINARY:
                        try:
                            if self._message_callback:
                                self._message_callback(msg.data)
                        except json.JSONDecodeError:
                            _LOGGER.error("Invalid JSON received from device %s: %s", 
                                        self.device_id, msg.data)
                    elif msg.type in (WSMsgType.ERROR, WSMsgType.CLOSED, WSMsgType.CLOSING):
                        # Handle connection termination messages
                        if msg.type == WSMsgType.ERROR:
                            _LOGGER.error("WebSocket connection closed with exception for device %s: %s", 
                                        self.device_id, self._client.exception())
                        else:
                            _LOGGER.info("WebSocket connection %s for device %s", 
                                       "closed" if msg.type == WSMsgType.CLOSED else "closing",
                                       self.device_id)
                        break
                except asyncio.TimeoutError:
                    # Timeout is not an error, continue waiting
                    continue
                except Exception as e:
                    _LOGGER.error("Error receiving WebSocket message for device %s: %s", 
                                self.device_id, e)
                    break
        except Exception as e:
            _LOGGER.error("Error in WebSocket receive loop for device %s: %s", 
                         self.device_id, e)
        finally:
            await self.async_disconnect()

    async def async_disconnect(self):
        """Close the WebSocket connection and cleanup resources."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        if self._client and not self._client.closed:
            await self._client.close()
        self._client = None

        if self._state_callback:
            self._state_callback(False)

    def start(self):
        """Start the WebSocket client and begin reconnection attempts."""
        if self.is_connected:
            _LOGGER.warning("WebSocket client for device %s is already connected", self.device_id)
            return
            
        self.hass.async_create_task(self._try_reconnect())
        _LOGGER.info("WebSocket client started for device %s", self.device_id)

    async def async_cleanup(self):
        """Clean up all resources and callbacks asynchronously."""
        await self.async_disconnect()
            
        # Clean up callbacks after disconnection
        self._message_callback = None
        self._state_callback = None
        
        _LOGGER.info("WebSocket client resources cleaned up for device %s", self.device_id)
        
    def cleanup(self):
        """Clean up all resources and callbacks (synchronous wrapper)."""
        self.hass.async_create_task(self.async_cleanup())

    async def _try_reconnect(self):
        """Attempt to reconnect to the device.
        
        If connection fails, wait 5 seconds before retrying.
        Only attempts reconnection if not currently connected.
        """
        if self.is_connected:
            _LOGGER.info("WebSocket client for device %s is already connected", self.device_id)
            return

        try:
            _LOGGER.info("Attempting to reconnect to device %s", self.device_id)
            connected = await self.async_connect()
            
            if connected:
                _LOGGER.info("Successfully reconnected to device %s", self.device_id)
                if self._state_callback:
                    self._state_callback(True)
                return
                
            _LOGGER.warning("Failed to reconnect to device %s", self.device_id)
            if self._state_callback:
                self._state_callback(False)
                
        except Exception as e:
            _LOGGER.error("Error during reconnection attempt for device %s: %s", self.device_id, e)
            if self._state_callback:
                self._state_callback(False)
                
        # If not connected, wait and retry
        if not self.is_connected:
            _LOGGER.info("Will retry reconnection to device %s in 5 seconds", self.device_id)
            await asyncio.sleep(5)
            self.hass.async_create_task(self._try_reconnect())

