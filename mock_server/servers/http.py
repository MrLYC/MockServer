# coding: utf-8

import logging
import base64

from tornado import httpserver
from tornado import web
from tornado import gen

from mock_server import SETTINGS
from mock_server import cache
from mock_server import utils
from mock_server.servers import MockCacheSchema

logger = logging.getLogger(__name__)


HTTP_SCHEMA = MockCacheSchema.register(
    "mock_http", "HTTP",
    {
        "method": {
            "type": "string",
            "enum": ["GET", "POST", "PUT", "DELETE", "HEADER", "PATCH"],
            "default": "GET",
        },
        "path": {
            "type": "string",
        },
        "query_string": {
            "type": "string",
            "multiple": True,
        },
        "http_header": {
            "type": "string",
            "multiple": True,
        },
    },
    {
        "data": {
            "type": "string",
            "default": "",
        },
        "data_type": {
            "type": "string",
            "default": "",
        },
        "status_code": {
            "type": "integer",
            "default": 200,
        },
        "status_reason": {
            "type": "string",
            "default": "",
        },
        "cookie": {
            "type": "string",
            "multiple": True,
        },
        "header": {
            "type": "string",
            "multiple": True,
        },
        "$ref": {
            "type": "string",
        },
    },
    [
        "X-MockServer-URI", "X-MockServer-Status",
    ]
)


class MockDataType(object):
    static_file = b"static_file"
    base64 = b"base64"


class MockHandler(web.RequestHandler):

    IDENT_HEDERS = {
        # "Accept": "",
    }

    def initialize(self):
        self.cache = cache.Cache()

    @gen.coroutine
    def service_static_file(self, response_info):
        with open(response_info.get(HTTP_SCHEMA.F_RSP_DATA), "rb") as fp:
            while True:
                chunk = fp.read(SETTINGS.BUFFER_SIZE)
                if not chunk:
                    break
                self.write(chunk)
                yield gen.Task(self.flush)

    @gen.coroutine
    def make_response_from_cache(self, uri):
        response_info = yield self.cache.get_data(
            uri=uri, patterns=[
                HTTP_SCHEMA.F_RSP_COOKIE,
                HTTP_SCHEMA.F_RSP_HEADER,
            ],
        )

        self.set_status(
            int(response_info.get(HTTP_SCHEMA.F_RSP_STATUS_CODE, 200)),
            response_info.get(HTTP_SCHEMA.F_RSP_STATUS_REASON),
        )
        for k, v in response_info.get(HTTP_SCHEMA.F_RSP_COOKIE, {}).items():
            self.set_cookie(k, v)

        for k, v in response_info.get(HTTP_SCHEMA.F_RSP_HEADER, {}).items():
            self.set_header(k, v)

        data_type = response_info.get(HTTP_SCHEMA.F_RSP_DATA_TYPE)
        data = response_info.get(HTTP_SCHEMA.F_RSP_DATA, "")
        if data_type == MockDataType.static_file:
            yield self.service_static_file(response_info)
        elif data_type == MockDataType.base64:
            self.write(base64.decodebytes(data))
        elif data:
            self.write(data)

    @gen.coroutine
    def handle_request(self, items):
        uri = utils.get_uri(HTTP_SCHEMA.schema, items)
        self.set_header(HTTP_SCHEMA.E_X_MOCKSERVER_URI, uri)
        self.set_header(HTTP_SCHEMA.E_X_MOCKSERVER_STATUS, "ok")
        try:
            yield self.make_response_from_cache(uri)
        except gen.Return:
            raise
        except Exception as err:
            self.set_header(HTTP_SCHEMA.E_X_MOCKSERVER_STATUS, str(err))
            logger.exception(err)

    def get_uri_items_from_request(self, request, **kwargs):
        kwargs.update({
            HTTP_SCHEMA.F_REQ_METHOD: self.request.method,
            HTTP_SCHEMA.F_REQ_PATH: self.request.path,
        })

        kwargs.update({
            "%s:%s" % (HTTP_SCHEMA.F_REQ_QUERY_STRING, k): ",".join(
                sorted(i.decode(SETTINGS.ENCODING) for i in v)
            )
            for k, v in self.request.query_arguments.items()
        })

        headers = self.request.headers
        kwargs.update({
            "%s:%s" % (HTTP_SCHEMA.F_REQ_HTTP_HEADER, k): headers.get(k, d)
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
