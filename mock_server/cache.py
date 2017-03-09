# coding: utf-8

import logging
from threading import RLock
from multiprocessing import pool

from tornado.concurrent import Future
from tornado import gen

from redis import Redis

from mock_server import SETTINGS

logger = logging.getLogger(__name__)


class CacheValue(object):
    true = b"1"
    false = b"0"

    t_raw = b""
    t_base64 = b"base64"
    t_static_file = b"static_file"


class SyncRedis(Redis):
    GLOBAL_INSTANCE = None
    GLOBAL_INIT_LOCK = RLock()

    @classmethod
    def get_global_instance(cls):
        if not cls.GLOBAL_INSTANCE:
            with cls.GLOBAL_INIT_LOCK:
                if not cls.GLOBAL_INSTANCE:
                    cls.GLOBAL_INSTANCE = cls(
                        SETTINGS.CACHE_ADDRESS, SETTINGS.CACHE_PORT,
                        SETTINGS.CACHE_DB,
                    )
        return cls.GLOBAL_INSTANCE

    def __init__(self, addr="localhost", port=6379, db=0):
        super(SyncRedis, self).__init__(addr, port, db)


class AsyncRedisCli(SyncRedis):
    GLOBAL_INSTANCE = None
    GLOBAL_INIT_LOCK = RLock()

    def __init__(self, addr, port=6379, db=0):
        super(AsyncRedisCli, self).__init__(addr, port, db)
        self.worker = pool.ThreadPool()

    def execute_command(self, *args, **kwargs):
        future = Future()
        self.worker.apply_async(
            super(AsyncRedisCli, self).execute_command,
            args=args, kwds=kwargs,
            callback=future.set_result,
            error_callback=future.set_exception,
        )
        return future


class Cache(object):
    PATTERN_SEP = ":"
    TEMPLATE_REF_KEY = "$ref"

    def __init__(self, redis_cli=None):
        self.redis_cli = redis_cli or AsyncRedisCli.get_global_instance()

    @gen.coroutine
    def _get_all(self, uri):
        uri_data = yield self.redis_cli.hgetall(uri)
        raise gen.Return({
            k.decode(SETTINGS.ENCODING): v
            for k, v in uri_data.items()
        })

    @gen.coroutine
    def delete_uri(self, uri):
        result = yield self.redis_cli.delete(uri)
        raise gen.Return(result)

    @gen.coroutine
    def delete_fields(self, uri, fields):
        result = yield self.redis_cli.hdel(uri, *fields)
        raise gen.Return(result)

    @gen.coroutine
    def list_uri_by_schema(self, schema):
        keys = yield self.redis_cli.keys("%s:*" % schema)
        logger.debug(keys)
        raise gen.Return([
            i.decode(SETTINGS.ENCODING)
            for i in keys
        ])

    @gen.coroutine
    def get_data(self, uri, patterns=None):
        uri_data = yield self._get_all(uri)
        data = {}
        template_uri = uri_data.get(self.TEMPLATE_REF_KEY)
        if template_uri and uri != template_uri.decode(SETTINGS.ENCODING):
            template_data = yield self.get_data(
                template_uri.decode(SETTINGS.ENCODING),
            )
            data.update(template_data)
        data.update(uri_data)
        if patterns:
            for k in list(i for i in data if i.find(self.PATTERN_SEP) > 0):
                type_, _, name = k.partition(self.PATTERN_SEP)
                if type_ not in patterns:
                    continue
                if type_ not in data:
                    data[type_] = {}
                item = data[type_]
                item[name] = data.pop(k)
        raise gen.Return(data)

    @gen.coroutine
    def set_data(self, uri, value, key=None):
        if key is not None:
            yield self.redis_cli.hset(uri, key, value)
        else:
            for k, v in value.items():
                yield self.redis_cli.hset(uri, k, v)
