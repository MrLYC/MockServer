# coding: utf-8

import logging
import base64

from tornado import tcpserver
from tornado import gen
from tornado.iostream import StreamClosedError

from mock_server import SETTINGS
from mock_server.cache import Cache
from mock_server import utils
from mock_server.servers import MockCacheSchema

logger = logging.getLogger(__name__)

TCP_SCHEMA = MockCacheSchema.register(
    "mock_tcp", "TCP",
    {
        "request": {
            "type": "string",
            "default": "",
        },
    },
    {
        "greeting": {
            "type": "string",
            "default": "",
        },
        "data": {
            "type": "string",
            "default": "",
        },
        "data_type": {
            "type": "string",
            "default": "",
        },
        "sep_regex": {
            "type": "string",
            "default": "",
        },
        "allow_empty_request": {
            "type": "boolean",
            "default": False,
        },
        "close_stream": {
            "type": "boolean",
            "default": False,
        },
    },
)


class MockTCPHandler(object):
    CACHE_BOOLEAN = {
        b"yes": True,
        b"no": False,
    }

    def __init__(self, stream, address, port, cache=None):
        self.stream = stream
        self.address = address
        self.port = port
        self.cache = cache or Cache()

    def on_close(self):
        self.stream.close()
        logger.info("stream[%s:%s] closed by client", self.address, self.port)

    def close_stream(self):
        self.stream.close()
        logger.info("stream[%s:%s] closed by server", self.address, self.port)

    def flush_stream(self):
        self.stream._handle_write()

    def make_uri_from_request(self, request, **kwargs):
        kwargs.update({
            TCP_SCHEMA.F_REQ_REQUEST: request,
        })
        return utils.get_uri(TCP_SCHEMA.schema, kwargs)

    @gen.coroutine
    def make_response(self, request):
        uri = self.make_uri_from_request(request)
        logger.info("uri: %s", uri)
        response_info = yield self.cache.get_data(uri)
        raise gen.Return(response_info)

    @gen.coroutine
    def run(self):
        stream = self.stream
        stream.set_close_callback(self.on_close)
        mock_tcp_config = yield self.cache.get_data(TCP_SCHEMA.schema)
        greeting = mock_tcp_config.get(TCP_SCHEMA.F_REQ_GREETING)
        sep_regex = mock_tcp_config.get(TCP_SCHEMA.F_REQ_SEP_REGEX, b"\n")
        allow_empty_request = self.CACHE_BOOLEAN.get(
            mock_tcp_config.get(TCP_SCHEMA.F_REQ_ALLOW_EMPTY_REQUEST), False,
        )

        try:
            if greeting:
                yield stream.write(greeting)

            while not stream.closed():
                request = yield stream.read_until_regex(sep_regex)
                if not request and not allow_empty_request:
                    self.close_stream()
                response_info = yield self.make_response(request)
                data = response_info.get(TCP_SCHEMA.F_REQ_DATA, b"")
                data_type = response_info.get(TCP_SCHEMA.F_REQ_DATA_TYPE)
                if data:
                    if data_type == b"base64":
                        data = base64.decodebytes(data)
                    yield stream.write(data)
                close_stream = self.CACHE_BOOLEAN.get(
                    response_info.get(TCP_SCHEMA.F_REQ_CLOSE_STREAM), False,
                )
                if close_stream:
                    self.close_stream()
        except StreamClosedError:
            pass


class MockTCPServer(tcpserver.TCPServer):

    @gen.coroutine
    def handle_stream(self, stream, address):
        handler = MockTCPHandler(stream, address[0], address[1])
        yield handler.run()


def init(server):
    server = MockTCPServer()
    server.listen(SETTINGS.PORT, SETTINGS.ADDRESS)
