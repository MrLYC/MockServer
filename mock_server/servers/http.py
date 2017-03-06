# coding: utf-8

import logging

from tornado import httpserver
from tornado import web
from tornado import gen

from mock_server import SETTINGS
from mock_server import cache
from mock_server import utils

logger = logging.getLogger(__name__)


class MockDataType(object):
    static_file = b"static_file"


class MockHandler(web.RequestHandler):
    IDENT_HEDERS = {
        # "Accept": "",
    }

    def initialize(self):
        self.cache = cache.Cahce()

    @gen.coroutine
    def service_static_file(self, response_info):
        with open(response_info.get("data"), "rb") as fp:
            while True:
                chunk = fp.read(SETTINGS.BUFFER_SIZE)
                if not chunk:
                    break
                self.write(chunk)
                yield gen.Task(self.flush)

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

        data_type = response_info.get("data_type")
        if data_type == MockDataType.static_file:
            yield self.service_static_file(response_info)
        else:
            self.write(response_info.get("data", ""))

    @gen.coroutine
    def handle_request(self, items):
        uri = utils.get_uri("mock_http", items)
        self.set_header("X-MockServer-URI", uri)
        self.set_header("X-MockServer-Status", "ok")
        try:
            yield self.make_response_from_cache(uri)
        except gen.Return:
            raise
        except Exception as err:
            self.set_header("X-MockServer-Status", str(err))
            logger.exception(err)

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
    application = web.Application(
        [
            (r".*?", MockHandler),
        ],
        debug=SETTINGS.DEBUG,
    )

    http_server = httpserver.HTTPServer(application)
    http_server.listen(SETTINGS.PORT, SETTINGS.ADDRESS)
