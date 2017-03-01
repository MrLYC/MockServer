# coding: utf-8

from mock_server import SETTINGS

from tornado import httpserver, web


class AdminHandler(web.RequestHandler):

    def get(self):
        self.write("ok!")


def init():
    application = web.Application([
        (r"/?", AdminHandler),
    ])

    http_server = httpserver.HTTPServer(application)
    http_server.listen(SETTINGS.PORT, SETTINGS.ADDRESS)
