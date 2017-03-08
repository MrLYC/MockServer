# coding: utf-8

import logging
import hashlib
import binascii
from collections import namedtuple

from mock_server import SETTINGS

logger = logging.getLogger(__name__)

UriInfo = namedtuple("UriInfo", [
    "schema", "fields", "items", "strict",
])


def get_uri_item(key, value, strict=False, encoding="utf-8"):
    if not isinstance(value, bytes):
        value = value.encode(encoding)

    if len(value) >= SETTINGS.AUTO_STRICT_ITEM_LENGTH and not strict:
        value = "~%s" % hashlib.md5(value).hexdigest()
    else:
        value = "".join("%x" % i for i in value)

    return "%s=%s" % (key, value)


def get_uri(schema, items, strict=False, encoding="utf-8"):
    paths = []
    keys = sorted(items.keys())
    for k in keys:
        paths.append(get_uri_item(k, items[k], strict, encoding))

    path = "/".join(paths)
    if len(path) > 255 and not strict:  # redis max key size
        path = get_uri_item("!", path, strict=False)

    return "%s:%s" % (schema, path)


def parse_uri_item(value, strict=False):
    if not value.startswith("~"):
        return binascii.unhexlify(value).decode("utf-8")
    return None


def parse_uri(uri):
    from pyparsing import (
        hexnums, nums, alphanums, Word, Literal,
        Optional, Forward, ZeroOrMore, Or, ParseException,
    )

    schema = Word(alphanums + "_-")
    schema_declare_char = Literal(":")
    key_declare_char = Literal("=")
    value = Word(nums + hexnums)
    value_type = Optional(Word("~-._", max=1), default="")
    value_item = (value_type + value)
    key = Word(alphanums + "_-:")
    hash_key = Word("!")
    item_sep = Literal("/")
    optional_item_sep = Optional(item_sep, default="/")
    item = Forward()
    item << ZeroOrMore(
        (key + key_declare_char + value_item + optional_item_sep) |
        (item_sep + item)
    )
    hash_item = hash_key + key_declare_char + value_item + optional_item_sep
    uri_parser = schema + schema_declare_char + Or(hash_item | item)

    try:
        uri_tokens = list(uri_parser.parseString(uri))
    except ParseException as err:
        raise ValueError(str(err))

    i_tokens = iter(uri_tokens)
    schema = next(i_tokens)
    strict = True
    fields = []
    items = {}
    next(i_tokens)
    for k, _, t, v, _ in zip(
        i_tokens, i_tokens, i_tokens, i_tokens, i_tokens,
    ):
        fields.append(k)
        if k == "!" or t != "":
            strict = False
        items[k] = "%s%s" % (t, v)

    return UriInfo(
        schema=schema, fields=fields,
        items=items, strict=strict,
    )
