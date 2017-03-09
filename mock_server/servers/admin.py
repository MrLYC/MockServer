# coding: utf-8

import logging

from jsonschema import Draft4Validator as Validator
from jsonschema.exceptions import ValidationError

from tornado import httpserver
from tornado import web
from tornado import gen
from tornado.escape import json_encode, json_decode

from mock_server import SETTINGS
from mock_server import cache
from mock_server import utils
from mock_server.servers import get_mock_schemas

logger = logging.getLogger(__name__)

SCHEMA_INFO = get_mock_schemas()


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

    def check_params(self, validator, params):
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
            result = []
            for schema in (
                request_params.get("schemas") or SCHEMA_INFO.keys()
            ):
                schema_info = SCHEMA_INFO.get(schema)
                if not schema_info:
                    continue
                items = yield self.cache.list_uri_by_schema(schema)
                schema_info = schema_info.as_dict()
                schema_info.update({
                    "items": items,
                })
                result.append(schema_info)
            self.write_json(result)
        except Exception as err:
            logger.exception(err)
            self.write_json(None, ok=False, message=str(err))


class ItemAdminHandler(ApiHandlerMixin, web.RequestHandler):
    POST_SCHEMAS = {
        s.schema: Validator(s.as_json_schema())
        for s in SCHEMA_INFO.values()
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
    def get_uri_info(self, uri, schema_info=None, **ex_data):
        data = yield self.cache.get_data(uri)
        if not data:
            raise gen.Return(None)
        uri_info = utils.parse_uri(uri)
        schema_info = schema_info or SCHEMA_INFO.get(uri_info.schema)
        result = {
            "uri": uri,
            "schema": schema_info.schema,
            "strict": uri_info.strict,
            "uri_info": {
                k: utils.parse_uri_item(v)
                for k, v in uri_info.items.items()
            },
            "items": {
                k: v.decode(SETTINGS.ENCODING)
                for k, v in data.items()
            }
        }
        result.update(ex_data)
        raise gen.Return(result)

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

        schema = params.get("schema")
        schema_info = SCHEMA_INFO.get(schema)
        json_schema = self.POST_SCHEMAS.get(schema_info.schema)
        if not json_schema or not schema_info:
            self.write_json(
                None, ok=False,
                message="unkonwn schema: %s" % schema,
            )
            raise gen.Return()

        error = self.check_params(json_schema, params)
        if error:
            self.write_json(None, ok=False, message=error)
            raise gen.Return()

        request_params = {}
        for k, v in params.items():
            if k in schema_info.request_fields:
                request_params[k] = v
            else:
                field, _, key = k.partition(":")
                field_info = schema_info.request_fields.get(field)
                if field_info and field_info.multiple:
                    request_params[k] = v
        uri = utils.get_uri(
            schema=schema_info.schema,
            items=request_params,
        )
        for k, v in params.items():
            yield self.cache.set_data(uri, v, k)
        uri_info = yield self.get_uri_info(uri, schema_info)
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
            (r"/api/schemas/?", SchemaAdminHandler),
            (r"/api/items/?", ItemAdminHandler),
        ],
        static_path=SETTINGS.STATIC_PATH,
        debug=SETTINGS.DEBUG,
    )

    http_server = httpserver.HTTPServer(application)
    http_server.listen(SETTINGS.PORT, SETTINGS.ADDRESS)
