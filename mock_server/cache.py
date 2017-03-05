# coding: utf-8

from threading import RLock
from itertools import chain

from multiprocessing import pool

from tornado.concurrent import Future
from tornado import gen

from redis import Redis

from mock_server import SETTINGS


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

    def __init__(self, addr, port=6379, db=0):
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


class Cahce(object):
    PATTERN_SEP = ":"
    TEMPLATE_REF_KEY = "$ref"

    def __init__(self, redis_cli=None):
        self.redis_cli = redis_cli or AsyncRedisCli.get_global_instance()

    @gen.coroutine
    def get_data(self, uri, patterns=None):
        data_list = []
        uri_data = yield self.redis_cli.hgetall(uri)
        data_list.insert(0, uri_data)
        template_uri = uri_data.get(self.TEMPLATE_REF_KEY)
        if template_uri:
            template_data = yield self.get_data(template_uri)
            data_list.insert(0, template_data)
        data = {
            k.decode(SETTINGS.ENCODING): v
            for k, v in chain(*(i.items() for i in data_list))
        }
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
