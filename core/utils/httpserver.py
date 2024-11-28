from tornado.web import Application
from tornado.httpserver import HTTPServer

from core.utils.singleton import Singleton


class HttpServer(Singleton, HTTPServer):
    """单例http服务"""

    def __init__(self, *args, **kwargs):
        super(Singleton, self).__init__(*args, **kwargs)
        super(HttpServer, self).__init__(*args, **kwargs)
        self._app = None

    @property
    def app(self) -> Application:
        return self._app

    @app.setter
    def app(self, app: Application):
        self._app = app
