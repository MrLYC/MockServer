# coding: utf-8


class MockField(object):
    def __init__(self, name, type, enum=None, default=None, multiple=False):
        self.name = name
        self.type = type
        self.enum = enum
        self.default = default
        self.multiple = multiple

    def __str__(self):
        return str(self.as_dict())

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        return {
            "name": self.name,
            "type": self.type,
            "multiple": self.multiple,
            "enum": self.enum,
            "default": self.default,
        }


class MockCacheSchema(object):
    REGISTERED_SCHEMAS = {}

    @classmethod
    def register(
        cls, schema, name, request_fields, response_fields, extend_headers=(),
    ):
        schema_instance = cls(
            schema=schema,
            name=name,
            request_fields={
                k: MockField(k, **i)
                for k, i in request_fields.items()
            },
            response_fields={
                k: MockField(k, **i)
                for k, i in response_fields.items()
            },
            extend_headers=extend_headers,
        )
        cls.REGISTERED_SCHEMAS[schema] = schema_instance
        return schema_instance

    def __init__(
        self, schema, name, request_fields, response_fields, **extend_attrs
    ):
        self.schema = schema
        self.name = name
        self.request_fields = request_fields
        self.response_fields = response_fields
        self.extend_attrs = extend_attrs

        for k in request_fields.keys():
            setattr(self, "F_REQ_%s" % k.upper().replace("-", "_"), k)

        for k in response_fields.keys():
            setattr(self, "F_RSP_%s" % k.upper().replace("-", "_"), k)

        for k, v in extend_attrs.items():
            setattr(self, "E_%s" % k.upper().replace("-", "_"), v)

    def __str__(self):
        return str(self.as_dict())

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        return {
            "schema": self.schema,
            "name": self.name,
            "request_fields": {
                k: i.as_dict()
                for k, i in self.request_fields.items()
            },
            "response_fields": {
                k: i.as_dict()
                for k, i in self.response_fields.items()
            },
        }


def get_mock_schemas():
    import importlib
    import os
    import re
    server_re = re.compile(r"^(?P<name>[^_].*?)\.py[dc]?$")
    for i in os.listdir(os.path.dirname(__file__)):
        match = server_re.search(i)
        if not match:
            continue
        info = match.groupdict()
        importlib.import_module("%s.%s" % (__name__, info["name"]))
    return MockCacheSchema.REGISTERED_SCHEMAS
