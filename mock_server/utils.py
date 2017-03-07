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
    return value


def parse_uri(uri):
    schema, _, paths = uri.partition(":")
    strict = True
    fields = []
    items = {}
    for i in paths.split("/"):
        key, _, value = i.partition("=")
        if strict:
            if key == "!" or value.startswith("~"):
                strict = False
        fields.append(key)
        items[key] = value
    return UriInfo(
        schema=schema, fields=fields,
        items=items, strict=strict,
    )
