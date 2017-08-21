# coding: utf-8

import six

from collections import OrderedDict

from tornado import gen

from mock_server import utils


class BaseSchema(object):

    @classmethod
    def force_text(s):
        if isinstance(s, six.string_types):
            return s
        return six.text_type(s)

    def __init__(self, name, cache, items=()):
        self.name = name
        self.cache = cache
        self.items = OrderedDict(items)

    def get_uri(self, data_item_keys):
        items = self.items.copy()
        items.update(data_item_keys)

        return utils.get_uri("%s://" % self.name, items)

    @gen.coroutine
    def get_data_gen(self, data_item_keys, data_key_patterns=None):
        uri = self.get_uri(data_item_keys)
        result = yield self.cache.get_data(uri, data_key_patterns)
        raise gen.Return(result)

    @gen.coroutine
    def set_data_gen(self, data_item_keys, **items):
        uri = self.get_uri(data_item_keys)
        result = yield self.cache.set_data(uri, items)
        raise gen.Return(result)

    def get_config_uri(self, namespaces):
        return utils.get_paths_uri("%s:" % self.name, namespaces)

    @gen.coroutine
    def get_config_gen(self, namespaces=(), patterns=None):
        uri = self.get_config_uri(namespaces)
        result = yield self.cache.get_data(uri, patterns)
        raise gen.Return(result)

    @gen.coroutine
    def set_config_gen(self, values, namespaces=(), update=False):
        uri = self.get_config_uri(namespaces)
        if update:
            result = yield self.cache.get_data()
            result.update(values)
            values = result
        yield self.cache.set_data(uri, values)
