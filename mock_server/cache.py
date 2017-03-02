# coding: utf-8

from threading import Rlock

from multiprocessing import pool

from tornado.concurrent import Future

import redis

from mock_server import SETTINGS


class AsyncRedisCli(redis.Redis):
    GLOBAL_INSTANCE = None
    GLOBAL_INIT_LOCK = Rlock()

    @classmethod
    def get_global_instance(cls):
        if not cls.GLOBAL_INSTANCE:
            with cls.GLOBAL_INIT_LOCK:
                if not cls.GLOBAL_INSTANCE:
                    cls.GLOBAL_INSTANCE = cls(
                        SETTINGS.ADDRESS, SETTINGS.PORT, SETTINGS.DB,
                    )
        return cls.GLOBAL_INSTANCE

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
