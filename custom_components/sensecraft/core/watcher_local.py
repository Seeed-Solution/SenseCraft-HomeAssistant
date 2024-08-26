import logging
from aiohttp import web
from homeassistant.core import HomeAssistant
from ..const import (
    DOMAIN,
)

class WebAppSingleton:
    _instance = None

    def __new__(cls, hass: HomeAssistant):
        if cls._instance is None:
            cls._instance = super(WebAppSingleton, cls).__new__(cls)
            cls._instance._initialized = False
            cls._instance.hass = hass
        return cls._instance

    def __init__(self, hass: HomeAssistant):
        if self._initialized:
            return
        self.hass = hass
        self._init_web_application()
        self._initialized = True

    def _init_web_application(self):
        """Initialize the web application and start listening on the port."""
        app = web.Application()
        app.router.add_post('/v1/notification/event', self.handle_request)

        runner = web.AppRunner(app)
        self.hass.loop.create_task(self._start_runner(runner))

    async def _start_runner(self, runner):
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8887)
        await site.start()

    async def handle_request(self, request):
        """Handle incoming HTTP POST request."""
        try:
            data = await request.json()
            eui = data.get('deviceEui')
            events = data.get('events')
            if eui is None or events is None:
                return web.json_response(
                    {'code': 11200, 'msg': "request parameters are invalid", 'data': {}})

            text = events.get('text')
            image = events.get('img')

            if text is not None:
                _event_type = ("{domain}_watcher_alarm_{eui}").format(
                    domain=DOMAIN,
                    eui=eui
                )
                self.hass.bus.fire(_event_type, {"text": text})

            if image is not None:
                _event_type = ("{domain}_watcher_image_{eui}").format(
                    domain=DOMAIN,
                    eui=eui
                )
                self.hass.bus.fire(_event_type, {"image": image})

            temperature = 'unavailable'
            humidity = 'unavailable'
            co2 = 'unavailable'

            sensorData = events.get('data')
            if sensorData is not None:
                sensor = sensorData.get('sensor')
                if sensor is not None:
                    temperature = sensor.get('temperature', 'unavailable')
                    humidity = sensor.get('humidity', 'unavailable')
                    co2 = sensor.get('CO2', 'unavailable')

            self.hass.bus.fire(("{domain}_watcher_temperature_{eui}").format(
                domain=DOMAIN,
                eui=eui,
            ), {"value": temperature})
            self.hass.bus.fire(("{domain}_watcher_humidity_{eui}").format(
                domain=DOMAIN,
                eui=eui,
            ), {"value": humidity})
            self.hass.bus.fire(("{domain}_watcher_co2_{eui}").format(
                domain=DOMAIN,
                eui=eui,
            ), {"value": co2})

            return web.json_response({'code': 200, 'msg': "", 'data': {}})

        except Exception as e:
            return web.json_response({'code': 11999, 'msg': "Illegal Input", 'data': {}})


class WatcherLocal():
    def __init__(self, hass: HomeAssistant, config: dict):
        self.hass = hass
        self.deviceId = config.get('device_id')

        self.connected = False

        WebAppSingleton(hass)

    def to_config(self):
        return {
            'device_id': self.deviceId,
        }

    @staticmethod
    def from_config(hass: HomeAssistant, config: dict):
        # 从字典创建对象
        local = WatcherLocal(hass, config)
        return local
