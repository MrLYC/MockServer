# coding: utf-8

import logging
import base64

from jsonschema import Draft4Validator as Validator
from jsonschema.exceptions import ValidationError

from tornado import httpserver
from tornado import web
from tornado import gen
from tornado.escape import json_encode, json_decode

from mock_server import SETTINGS
from mock_server import cache
from mock_server import utils

logger = logging.getLogger(__name__)


class IndexHandler(web.StaticFileHandler):
    FILE_PATH = "html/index.html"

    def initialize(self):
        super(IndexHandler, self).initialize(SETTINGS.STATIC_PATH)

    @gen.coroutine
    def get(self):
        yield super(IndexHandler, self).get(self.FILE_PATH)

    post = get


class ApiHandlerMixin(object):

    def initialize(self):
        self.cache = cache.Cache()

    def get_request_params(self):
        return {}

    def check_params(self, validate_schema, params):
        validator = Validator(validate_schema)
        try:
            validator.validate(params)
        except ValidationError as err:
            return str(err)
        return None

    def write_json(self, data, ok=True, message=None, **kwargs):
        self.set_header("Content-type", "application/json")
        kwargs.update({
            "ok": ok,
            "message": message,
            "data": data,
        })
        self.write(json_encode(kwargs))


class SchemaAdminHandler(ApiHandlerMixin, web.RequestHandler):

    def get_request_params(self):
        return {
            "schemas": [
                i.decode(SETTINGS.ENCODING)
                for i in self.request.arguments.get("schema") or ()
            ],
        }

    @gen.coroutine
    def get(self):
        try:
            request_params = self.get_request_params()
            data = {}
            for schema in request_params.get("schemas") or ():
                items = yield self.cache.list_uri_by_schema(schema)
                data[schema] = items
            self.write_json(data)
        except Exception as err:
            logger.exception(err)
            self.write_json(None, ok=False, message=str(err))


class ItemAdminHandler(ApiHandlerMixin, web.RequestHandler):
    SCHEMA_ITEMS = {
        "mock_http": {},
        "mock_tcp": {},
    }
    POST_SCHEMA = {
        "type": "object",
        "required": ["schema", "request", "response"],
        "properties": {
            "schema": {
                "type": "string",
                "enum": ["mock_tcp", "mock_http"],
            },
            "response_type": {
                "type": "string",
                "enum": ["raw", "base64"],
            },
            "response_encoding": {
                "type": "string",
            },
            "request": {
                "type": "object",
                "minProperties": 1,
            },
            "response": {
                "type": "object",
                "minProperties": 1,
            },
        },
    }

    def get_request_params(self):
        return {
            "uri_list": [
                i.decode(SETTINGS.ENCODING)
                for i in self.request.arguments.get("uri") or ()
            ],
            "field_list": [
                i.decode(SETTINGS.ENCODING)
                for i in self.request.arguments.get("field") or ()
            ],
        }

    @gen.coroutine
    def get_uri_info(self, uri, **ex_data):
        data = yield self.cache.get_data(uri)
        if not data:
            raise gen.Return(None)
        uri_info = utils.parse_uri(uri)
        uri_data = self.SCHEMA_ITEMS.get(uri_info.schema, {}).copy()
        uri_data["uri"] = uri
        uri_data["schema"] = uri_info.schema
        uri_data.update({
            k: base64.encodestring(v).decode(SETTINGS.ENCODING)
            for k, v in data.items()
        })
        uri_data.update(ex_data)
        raise gen.Return(uri_data)

    @gen.coroutine
    def get(self):
        try:
            request_params = self.get_request_params()
            uri_list = []
            for uri in request_params.get("uri_list") or ():
                uri_info = yield self.get_uri_info(uri)
                if uri_info is not None:
                    uri_list.append(uri_info)
            self.write_json(uri_list)
        except Exception as err:
            logger.exception(err)
            self.write_json(None, ok=False, message=str(err))

    @gen.coroutine
    def post(self):
        try:
            params = json_decode(self.request.body)
        except (TypeError, ValueError):
            self.write_json(None, ok=False, message="parse json failed")
            raise gen.Return()

        error = self.check_params(self.POST_SCHEMA, params)
        if error:
            self.write_json(None, ok=False, message=error)
            raise gen.Return()

        uri = utils.get_uri(
            schema=params.get("schema"),
            items=params.get("request"),
        )
        response_type = params.get("response_type").decode(SETTINGS.ENCODING)
        response_encoding = params.get("response_encoding", SETTINGS.ENCODING)
        for k, v in params.get("response").items():
            if response_type == "base64":
                data = base64.decodestring(v.encode(response_encoding))
            else:
                data = v
            yield self.cache.set_data(uri, data, k)
        uri_info = yield self.get_uri_info(uri)
        self.write_json(uri_info)

    @gen.coroutine
    def delete(self):
        try:
            request_params = self.get_request_params()
            for uri in request_params.get("uri_list") or ():
                uri_info = yield self.get_uri_info(uri)
                if uri_info is None:
                    continue
                field_list = request_params.get("field_list")
                if not field_list:
                    yield self.cache.delete_uri(uri)
                else:
                    yield self.cache.delete_fields(uri, field_list)
        except Exception as err:
            logger.exception(err)
            self.write_json(None, ok=False, message=str(err))


def init(server):
    application = web.Application(
        [
            (r"/?", IndexHandler),
            (r"/schemas/?", SchemaAdminHandler),
            (r"/items/?", ItemAdminHandler),
        ],
        static_path=SETTINGS.STATIC_PATH,
        debug=SETTINGS.DEBUG,
    )

    http_server = httpserver.HTTPServer(application)
    http_server.listen(SETTINGS.PORT, SETTINGS.ADDRESS)
