# coding: utf-8

import hashlib


def get_uri(schema, items, strict=False, encoding="utf-8"):
    paths = []
    for k, v in items.items():
        if not isinstance(v, bytes):
            v = v.encode(encoding)

        if len(v) >= 16 and not strict:
            v = hashlib.md5(v).hexdigest()
        else:
            v = "#%s" % "".join("%x" % i for i in v)

        paths.append("%s=%s" % (k, v))

    return "%s:%s" % (schema, "/".join(paths))
