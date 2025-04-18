import logging
from aiohttp import web
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

class HTTPClient:
    """HTTP Server client for device communication."""
    _instance = None
    _port = 8887  # 统一使用8887端口

    RECAMERA_STATE_PATH = '/recamera/state'
    WATCHER_STATE_PATH = '/v1/notification/event'

    def __new__(cls, hass: HomeAssistant):
        if cls._instance is None:
            cls._instance = super(HTTPClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, hass: HomeAssistant):
        if self._initialized:
            return
        self.hass = hass
        self.handlers = {
            self.RECAMERA_STATE_PATH: None,
            self.WATCHER_STATE_PATH: None
        }
        self.app = None
        self.runner = None
        self.site = None
        self._initialized = True
        self.hass.async_create_task(self._init_server())
        _LOGGER.info("HTTPClient initialized")

    async def _init_server(self):
        """Initialize and start the web server."""
        try:
            self.app = web.Application()
            
            # 注册所有固定路由
            self.app.router.add_post(self.RECAMERA_STATE_PATH, self.handle_request)
            self.app.router.add_post(self.WATCHER_STATE_PATH, self.handle_request)
            
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, '0.0.0.0', self._port)
            await self.site.start()
            _LOGGER.info("HTTP server started on port %d with predefined routes", self._port)
        except Exception as e:
            _LOGGER.error("Failed to start HTTP server: %s", e)

    async def handle_request(self, request):
        """Handle incoming HTTP POST request."""
        try:
            path = request.path
            handler = self.handlers.get(path)
            
            if handler is not None:
                try:
                    # 调用处理函数并获取结果
                    result = await handler(request)
                    # 如果处理函数返回了错误码和消息，使用它们
                    if isinstance(result, dict) and 'code' in result and 'msg' in result:
                        return web.json_response(result)
                    # 否则返回成功响应
                    return web.json_response({
                        'code': 200,
                        'msg': "Success",
                        'data': result if result is not None else {}
                    })
                except Exception as e:
                    _LOGGER.error("Error in handler for path %s: %s", path, e)
                    return web.json_response({
                        'code': 11999,
                        'msg': str(e),
                        'data': {}
                    })
            _LOGGER.warning("No handler registered for path: %s", path)
            return web.json_response({
                'code': 404,
                'msg': "Handler not registered",
                'data': {}
            })
        except Exception as e:
            _LOGGER.error("Error handling request: %s", e)
            return web.json_response({
                'code': 11999,
                'msg': "Illegal Input",
                'data': {}
            }) 