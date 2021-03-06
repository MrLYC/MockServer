# coding: utf-8

import logging
import base64
import os

from tornado import httpserver
from tornado import web
from tornado import gen

from mock_server import SETTINGS
from mock_server import utils
from mock_server.cache import Cache, CacheValue
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
            "pattern": r"^([^?#]*)?$",
        },
        "body": {
            "type": "string",
        },
        "query_string": {
            "type": "string",
            "multiple": True,
            "pattern": r"^([^#]*)?$",
        },
        "http_header": {
            "type": "string",
            "multiple": True,
        },
    },
    {
        "name": {
            "type": "string",
        },
        "data": {
            "type": "string",
            "rich_text": True,
        },
        "data_type": {
            "type": "string",
            "enum": ["raw", "static_file", "base64"],
            "default": "raw",
        },
        "status_code": {
            "type": "number",
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
        Cache.TEMPLATE_REF_KEY: {
            "type": "string",
        },
    },
    E_X_MOCKSERVER_URI="X-MockServer-URI",
    E_X_MOCKSERVER_STATUS="X-MockServer-Status",
)


class MockHandler(web.RequestHandler):

    IDENT_HEDERS = {
        # "Accept": "",
    }

    def initialize(self):
        self.cache = Cache()

    @gen.coroutine
    def service_static_file(self, response_info):
        data = response_info.get(HTTP_SCHEMA.F_RSP_DATA)
        if data:
            data = data.decode(SETTINGS.ENCODING)
        else:
            data = "data.dat"

        path = os.path.join(SETTINGS.STATIC_PATH, data)
        with open(path, "rb") as fp:
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
        if data_type == CacheValue.t_static_file:
            yield self.service_static_file(response_info)
        elif data_type == CacheValue.t_base64:
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

        kwargs[HTTP_SCHEMA.F_REQ_BODY] = request.body

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
