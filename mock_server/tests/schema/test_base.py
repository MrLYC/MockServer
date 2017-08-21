# coding: utf-8

from mock_server.tests import mock_test, AsyncTestCase

from mock_server.schema import base
from mock_server import cache


class TestBaseSchema(AsyncTestCase):

    @mock_test
    def test_config(self):
        schema = base.BaseSchema("test", cache.Cache())
        yield schema.set_config_gen({
            "a": 1, "b": "2",
        })
        result = yield schema.get_config_gen()
        self.assertEqual(result["a"], b"1")
        self.assertEqual(result["b"], b"2")
