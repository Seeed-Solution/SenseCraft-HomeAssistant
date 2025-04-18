"""Watcher platform for Sensecraft."""
import logging
import os
import aiofiles
from base64 import b64decode
from datetime import datetime, timedelta
from homeassistant.core import HomeAssistant
from .http_client import HTTPClient
from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class Watcher():
    def __init__(self, hass: HomeAssistant, config: dict):
        """Initialize the Watcher instance.

        Args:
            hass: Home Assistant instance
            config: Configuration dictionary containing device settings
        """
        self.hass = hass
        self.deviceId = config.get('device_id')
        self.connected = False

        # Image retention settings
        self.max_images = 10000  # Maximum number of images to keep
        self.retention_days = 30  # Number of days to keep images
        self.image_dir = self.hass.config.path('www/images')

        # Initialize HTTP client
        self.http_client = HTTPClient(hass)
        self.http_client.handlers[HTTPClient.WATCHER_STATE_PATH] = self.handle_http_request
        _LOGGER.info("Watcher initialized with device ID: %s", self.deviceId)

    async def cleanup_old_images(self):
        """Clean up old images based on retention policy."""
        try:
            if not os.path.exists(self.image_dir):
                return

            # Calculate cutoff time for retention period
            cutoff_time = datetime.now() - timedelta(days=self.retention_days)

            # Get list of image files
            files_to_remove = []
            valid_files = []

            # List directory contents
            dir_contents = await self.hass.async_add_executor_job(os.listdir, self.image_dir)

            # First pass: identify expired files and collect valid files
            for f in dir_contents:
                if f.startswith('watcher_') and f.endswith('.png'):
                    full_path = os.path.join(self.image_dir, f)
                    # Get file modification time
                    mtime = os.path.getmtime(full_path)
                    file_time = datetime.fromtimestamp(mtime)

                    if file_time < cutoff_time:
                        # File is older than retention period
                        files_to_remove.append(full_path)
                        _LOGGER.debug("Marked for removal (expired): %s (age: %s)",
                                      full_path, file_time)
                    else:
                        # File is within retention period
                        valid_files.append((full_path, mtime))

            _LOGGER.debug("Total image files: %d, Valid files: %d, Expired files: %d",
                          len(dir_contents), len(valid_files), len(files_to_remove))

            # Sort valid files by modification time (oldest first)
            valid_files.sort(key=lambda x: x[1])

            # If we have more valid files than max_images, remove the oldest ones
            if len(valid_files) > self.max_images:
                # Calculate how many more files to remove
                excess_count = len(valid_files) - self.max_images

                # Add the oldest files to the removal list
                for i in range(excess_count):
                    file_path = valid_files[i][0]
                    files_to_remove.append(file_path)
                    _LOGGER.debug("Marked for removal (excess): %s", file_path)

            # Now remove all marked files
            for file_path in files_to_remove:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        _LOGGER.debug("Removed image: %s", file_path)
                    else:
                        _LOGGER.debug("File already removed: %s", file_path)
                except Exception as e:
                    _LOGGER.error("Error removing file %s: %s", file_path, e)

        except Exception as e:
            _LOGGER.error("Error cleaning up old images: %s", e)

    async def save_image_to_file(self, image_base64, filename):
        """Save base64 image to file."""
        try:
            image_data = b64decode(image_base64)
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            async with aiofiles.open(filename, 'wb') as file:
                await file.write(image_data)
            return True
        except Exception as e:
            _LOGGER.error("Failed to save image to file %s: %s", filename, e)
            return False

    async def handle_http_request(self, request):
        """Handle incoming HTTP request for Watcher."""
        try:
            data = await request.json()
            eui = data.get('deviceEui')
            events = data.get('events')
            if eui is None or events is None:
                return {
                    'code': 11200,
                    'msg': "Invalid parameters",
                    'data': {}
                }

            # Handle text events
            if text := events.get('text'):
                self.hass.bus.fire(
                    f"{DOMAIN}_watcher_{eui}_alarm", {"text": text})

            # Handle image events
            if image := events.get('img'):
                # Schedule cleanup as a background task instead of awaiting it
                self.hass.create_task(self.cleanup_old_images())

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                filename = os.path.join(
                    self.image_dir, f'watcher_{timestamp}.png')
                if await self.save_image_to_file(image, filename):
                    self.hass.bus.fire(f"{DOMAIN}_watcher_{eui}_image", {
                        "image_path": filename,
                        "alarm_text": text if text is not None else ""
                    })
                else:
                    _LOGGER.error("Failed to save image for device %s", eui)

            # Handle sensor data
            if sensor_data := events.get('data', {}).get('sensor', {}):
                for sensor_type in ['temperature', 'humidity', 'CO2']:
                    value = sensor_data.get(sensor_type, 'unavailable')
                    self.hass.bus.fire(
                        f"{DOMAIN}_watcher_{eui}_{sensor_type.lower()}", {"value": value})

            return {}  # Return empty data on success

        except Exception as e:
            _LOGGER.error("Error handling Watcher request: %s", e)
            return {
                'code': 11999,
                'msg': str(e),
                'data': {}
            }

    def to_config(self):
        """Convert current configuration to dictionary format.

        Returns:
            dict: Current device configuration
        """
        return {'device_id': self.deviceId}

    @staticmethod
    def from_config(hass: HomeAssistant, config: dict):
        """Create Watcher instance from configuration.

        Args:
            hass: Home Assistant instance
            config: Configuration dictionary

        Returns:
            Watcher: New Watcher instance
        """
        return Watcher(hass, config)

    def cleanup(self):
        """Clean up all resources and unregister handlers."""
        # Remove handler
        if self.http_client.handlers[HTTPClient.WATCHER_STATE_PATH] == self.handle_http_request:
            self.http_client.handlers[HTTPClient.WATCHER_STATE_PATH] = None
        _LOGGER.info("Watcher resources cleaned up")
