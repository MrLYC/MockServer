# coding: utf-8

from threading import RLock

from multiprocessing import pool

from tornado.concurrent import Future

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

    def __init__(self, addr, port=6379, db=0, **kwargs):
        super(SyncRedis, self).__init__(
            host=addr, port=port, db=db, **kwargs
        )


class AsyncRedisCli(SyncRedis):
    GLOBAL_INSTANCE = None
    GLOBAL_INIT_LOCK = RLock()

    def __init__(self, addr, port=6379, db=0, **kwargs):
        super(AsyncRedisCli, self).__init__(addr, port, db, **kwargs)
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
