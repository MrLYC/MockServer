# coding: utf-8

import logging

from tornado import httpserver
from tornado import web
from tornado import gen

from mock_server import SETTINGS
from mock_server import cache
from mock_server import utils

logger = logging.getLogger(__name__)


class MockHandler(web.RequestHandler):

    def initialize(self):
        self.redis_cli = cache.AsyncRedisCli.get_global_instance()

    @gen.coroutine
    def make_response_from_cache(self, key):
        body = yield self.redis_cli.hget(key, "body")
        logger.debug("body: %s", body)
        self.write(body or "")

    @gen.coroutine
    def handle_request(self, items):
        uri = utils.get_uri("mock_http", items)
        logger.info("uri: %s", uri)
        yield self.make_response_from_cache(uri)

    def get_uri_items_from_request(self, request, **kwargs):
        kwargs.update({
            "method": self.request.method,
            "path": self.request.path,
        })
        for k, v in self.request.query_arguments.items():
            kwargs.update("qs_%s" % k, v, SETTINGS.CACHE_STRICT_MODE)
        return kwargs

    @web.asynchronous
    @gen.coroutine
    def get(self):
        yield self.handle_request(self.get_uri_items_from_request(
            self.request,
        ))


def init():
    application = web.Application([
        (r".*?", MockHandler),
    ])

    http_server = httpserver.HTTPServer(application)
    http_server.listen(SETTINGS.PORT, SETTINGS.ADDRESS)
