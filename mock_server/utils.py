# coding: utf-8

import hashlib
from collections import namedtuple

UriInfo = namedtuple("UriInfo", [
    "schema", "fields", "items", "strict",
])


def get_uri_item(key, value, strict=False, encoding="utf-8"):
    if not isinstance(value, bytes):
        value = value.encode(encoding)

    if len(value) >= 16 and not strict:  # choice a shortest result
        value = hashlib.md5(value).hexdigest()
    else:
        value = "~%s" % "".join("%x" % i for i in value)

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


def parse_uri(uri):
    schema, _, paths = uri.partition(":")
    strict = True
    fields = []
    items = {}
    for i in paths.split("/"):
        key, _, value = i.partition("=")
        if strict:
            if key == "!" or not value.startswith("~"):
                strict = False
        fields.append(key)
        items[key] = value
    return UriInfo(
        schema=schema, fields=fields,
        items=items, strict=strict,
    )
