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
    IDENT_HEDERS = {
        # "Accept": "",
    }

    def initialize(self):
        self.cache = cache.Cahce()

    @gen.coroutine
    def make_response_from_cache(self, uri):
        response_info = yield self.cache.get_data(
            uri=uri, patterns=["cookie", "header"],
        )

        self.set_status(
            int(response_info.get("status_code", 200)),
            response_info.get("status_reason"),
        )
        for k, v in response_info.get("cookie", {}).items():
            self.set_cookie(k, v)

        for k, v in response_info.get("header", {}).items():
            self.set_header(k, v)

        self.write(response_info.get("body", ""))

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

        kwargs.update({
            "query_string:%s" % k: ",".join(
                sorted(i.decode(SETTINGS.ENCODING) for i in v)
            )
            for k, v in self.request.query_arguments.items()
        })

        headers = self.request.headers
        kwargs.update({
            "http_header:%s" % k: headers.get(k, d)
            for k, d in self.IDENT_HEDERS.items()
        })
        return kwargs

    @web.asynchronous
    @gen.coroutine
    def _idempotent_method(self):
        yield self.handle_request(self.get_uri_items_from_request(
            self.request,
        ))

    @web.asynchronous
    @gen.coroutine
    def _nonidempotent_method(self):
        yield self.handle_request(self.get_uri_items_from_request(
            self.request,
            body=self.request.body,
        ))

    get = _idempotent_method
    delete = _idempotent_method
    head = _idempotent_method
    post = _nonidempotent_method
    put = _nonidempotent_method
    patch = _nonidempotent_method


def init(server):
    application = web.Application([
        (r".*?", MockHandler),
    ])

    http_server = httpserver.HTTPServer(application)
    http_server.listen(SETTINGS.PORT, SETTINGS.ADDRESS)
