"""ReCamera platform for Sensecraft."""
import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .http_client import HTTPClient
from .ws_client import WSClient

_LOGGER = logging.getLogger(__name__)


class ReCamera():
    """ReCamera platform implementation for Sensecraft devices."""

    def __init__(self, hass: HomeAssistant, config: dict):
        """Initialize the ReCamera instance.
        
        Args:
            hass: Home Assistant instance
            config: Configuration dictionary containing device settings
        """
        self.hass = hass
        self.deviceId = config.get('device_id')
        self.deviceHost = config.get('device_host')
        self.deviceName = f"sensecraft_recamera_{self.deviceId}"

        self.connected = False
        self.classes = []
        self._camera_callback = None
        self._event_update_yaw_angle = f"sensecraft_recamera_{self.deviceId}_{0x141}_angle"
        self._event_update_pitch_angle = f"sensecraft_recamera_{self.deviceId}_{0x142}_angle"
        self._event_update_tracking_target = f"sensecraft_recamera_{self.deviceId}_tracking_target"
        self._event_update_tracking_enable = f"sensecraft_recamera_{self.deviceId}_tracking_enable"

        # WebSocket client instance
        self.ws_client = None

        # Initialize HTTP client singleton and register handler
        self.http_client = HTTPClient(hass)
        self.http_client.handlers[HTTPClient.RECAMERA_STATE_PATH] = self.handle_http_request
        _LOGGER.info("ReCamera initialized with device ID: %s", self.deviceId)

    async def async_test_connection(self) -> bool:
        """Test the connection to the device.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if not self.deviceHost:
            _LOGGER.error("Cannot connect: device host not configured")
            return False

        try:
            # Create temporary WebSocket client for testing
            client = WSClient(self.hass, self.deviceId, self.deviceHost)

            # Attempt connection
            connected = await client.async_connect()

            # Clean up resources regardless of connection result
            await client.async_disconnect()

            return connected
        except Exception as e:
            _LOGGER.error(
                "Failed to test connection to device %s: %s", self.deviceId, e)
            return False

    async def async_setup(self) -> bool:
        """Set up the device connection for async_setup_entry initialization.
        
        Establishes persistent connection, sets up callbacks, and starts auto-reconnection.
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        if not self.deviceHost:
            _LOGGER.error("Cannot connect: device host not configured")
            return False

        try:
            # Initialize WebSocket client if not exists
            if not self.ws_client:
                self.ws_client = WSClient(
                    self.hass, self.deviceId, self.deviceHost)
                # Configure callbacks
                self.ws_client._message_callback = self._handle_ws_message
                self.ws_client._state_callback = self._handle_ws_state

            self.ws_client.start()

            return True  # Return True to let reconnection mechanism handle subsequent connections
        except Exception as e:
            _LOGGER.error("Failed to setup device %s: %s", self.deviceId, e)
            return False

    async def async_disconnect(self):
        """Disconnect from the device and cleanup resources."""
        if self.ws_client:
            await self.ws_client.async_disconnect()
            self.ws_client = None
        self.connected = False

    def update_config(self, new_config: dict):
        """Update device configuration.
        
        Args:
            new_config: New configuration dictionary
        """
        if 'device_host' in new_config:
            old_host = self.deviceHost
            self.deviceHost = new_config['device_host']

            # Update WebSocket connection if host changed
            if old_host != self.deviceHost:
                self.hass.async_create_task(self._reconnect())

    async def _reconnect(self):
        """Reconnect to the device with current configuration."""
        await self.async_disconnect()
        if self.deviceHost:
            await self.async_setup()

    def to_config(self):
        """Convert current configuration to dictionary format.
        
        Returns:
            dict: Current device configuration
        """
        return {
            'device_id': self.deviceId,
            'device_host': self.deviceHost,
        }

    @staticmethod
    def from_config(hass: HomeAssistant, config: dict):
        """Create ReCamera instance from configuration.
        
        Args:
            hass: Home Assistant instance
            config: Configuration dictionary
            
        Returns:
            ReCamera: New ReCamera instance
        """
        return ReCamera(hass, config)

    async def handle_http_request(self, request):
        """Handle incoming HTTP requests for ReCamera.
        
        Args:
            request: HTTP request object
            
        Returns:
            dict: Response data or error information
        """
        try:
            data = await request.json()
            device_id = data.get('sn')
            if device_id != self.deviceId:
                return {
                    'code': 400,
                    'msg': "Device ID mismatch",
                    'data': {}
                }

            event_type = data.get('state')
            event_data = data.get('data')
            if event_type == 'update_angle':
                motor_id = event_data.get('motor_id')
                if motor_id == 0x141:
                    self.hass.bus.fire(
                        self._event_update_yaw_angle,
                        {"data": event_data}
                    )
                elif motor_id == 0x142:
                    self.hass.bus.fire(
                        self._event_update_pitch_angle,
                        {"data": event_data}
                    )
            elif event_type == 'update_tracking_target':
                self.hass.bus.fire(
                    self._event_update_tracking_target,
                    {"data": event_data}
                )
            elif event_type == 'update_tracking_enable':
                self.hass.bus.fire(
                    self._event_update_tracking_enable,
                    {"data": event_data}
                )

            return {}  # Return empty data on success

        except Exception as e:
            _LOGGER.error("Error handling ReCamera request: %s", e)
            return {
                'code': 500,
                'msg': str(e),
                'data': {}
            }

    async def send_control(self, command_data):
        """Send control command to device via HTTP.
        
        Args:
            command_data: Command data to send
            
        Returns:
            dict: Response data or None if failed
        """
        if not self.deviceHost:
            _LOGGER.error("Device host not configured")
            return None

        try:
            request_data = {
                'sn': self.deviceId,
                'command_data': command_data,
            }

            session = async_get_clientsession(self.hass)
            url = f"http://{self.deviceHost}:1880/recamera/control"
            _LOGGER.info("Sending control command to %s: %s",
                         url, request_data)

            async with session.post(url, json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    _LOGGER.info("Control command response: %s", result)
                    return result
                else:
                    _LOGGER.error("Failed to send control command: %s", await response.text())
                    return None
        except Exception as e:
            _LOGGER.error("Error sending control command: %s", e)
            return None

    def _handle_ws_message(self, data):
        """Handle incoming WebSocket messages.
        
        Args:
            data: Message data received from WebSocket
        """
        try:
            if self._camera_callback:
                self._camera_callback(data)
        except Exception as e:
            _LOGGER.error("Error handling WebSocket message: %s", e)

    def _handle_ws_state(self, connected: bool):
        """Handle WebSocket connection state changes.
        
        Args:
            connected: New connection state
        """
        self.connected = connected

        # Broadcast connection state change through event bus
        self.hass.bus.fire(
            f"sensecraft_recamera_{self.deviceId}_connection_state",
            {"connected": connected}
        )

        _LOGGER.info("WebSocket connection state changed for device %s: %s",
                     self.deviceId, "connected" if connected else "disconnected")

    def on_received_camera_image(self, callback):
        """Set callback for image monitoring.
        
        Args:
            callback: Callback function to handle received images
        """
        self._camera_callback = callback

    def cleanup(self):
        """Clean up all resources and unregister handlers."""
        if self.http_client.handlers[HTTPClient.RECAMERA_STATE_PATH] == self.handle_http_request:
            self.http_client.handlers[HTTPClient.RECAMERA_STATE_PATH] = None

        self.hass.async_create_task(self.async_disconnect())

        _LOGGER.info("ReCamera resources cleaned up")
