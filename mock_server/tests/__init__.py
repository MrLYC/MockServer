# coding: utf-8

from tornado.testing import gen_test, AsyncTestCase


def mock_test(f):
    @gen_test
    def test_case(*args, **kwargs):
        return f(*args, **kwargs)
    return test_case
