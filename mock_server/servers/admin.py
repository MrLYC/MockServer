# coding: utf-8

from mock_server import SETTINGS

from tornado import httpserver
from tornado import web
from tornado import gen


class IndexHandler(web.StaticFileHandler):
    FILE_PATH = "html/index.html"

    def initialize(self):
        super(IndexHandler, self).initialize(SETTINGS.STATIC_PATH)

    @gen.coroutine
    def get(self):
        yield super(IndexHandler, self).get(self.FILE_PATH)

    post = get


def init(server):
    application = web.Application(
        [
            (r"/?", IndexHandler),
        ],
        static_path=SETTINGS.STATIC_PATH,
        debug=SETTINGS.DEBUG,
    )

    http_server = httpserver.HTTPServer(application)
    http_server.listen(SETTINGS.PORT, SETTINGS.ADDRESS)
