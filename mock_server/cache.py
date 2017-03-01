# coding: utf-8

from multiprocessing import pool

from tornado.concurrent import Future

import redis

from mock_server import SETTINGS


class AsyncRedisCli(redis.Redis):

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
