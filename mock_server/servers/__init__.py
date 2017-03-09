# coding: utf-8

import re

undefined = frozenset("undefined")


class MockField(object):

    def __init__(
        self, name, type, enum=None, default=undefined,
        multiple=False, rich_text=False,
    ):
        self.name = name
        self.type = type
        self.enum = enum
        self.default = default
        self.multiple = multiple
        self.rich_text = rich_text

    @property
    def field_regex(self):
        if self.multiple:
            return "^%s:" % self.name
        return "^%s$" % self.name

    def __str__(self):
        return str(self.as_dict())

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        info = {
            "name": self.name,
            "type": self.type,
            "multiple": self.multiple,
            "enum": self.enum,
            "rich_text": self.rich_text,
        }
        if self.default is not undefined:
            info["default"] = self.default
        return info

    def as_json_schema(self):
        schema = {
            "type": self.type,
        }
        if self.default is not undefined:
            schema["default"] = self.default
        if self.enum:
            schema["enum"] = self.enum
        return schema


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
        self.required_fields = set()

        for k, f in request_fields.items():
            if f.default is not undefined:
                self.required_fields.add(f)
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

    def as_json_schema(self):
        properties = {
            "schema": {
                "type": "string",
            },
        }
        pattern_properties = {}
        schema = {
            "type": "object",
            "required": [f.name for f in self.required_fields],
            "properties": properties,
            "additionalProperties": False,
        }

        for f in self.request_fields.values():
            sch = f.as_json_schema()
            if f.multiple:
                pattern_properties[f.field_regex] = sch
            else:
                properties[f.name] = sch

        for f in self.response_fields.values():
            sch = f.as_json_schema()
            if f.multiple:
                pattern_properties[f.field_regex] = sch
            else:
                properties[f.name] = sch

        if pattern_properties:
            schema["patternProperties"] = pattern_properties

        return schema


def get_mock_schemas():
    import importlib
    import os
    server_re = re.compile(r"^(?P<name>[^_].*?)\.py[dc]?$")
    for i in os.listdir(os.path.dirname(__file__)):
        match = server_re.search(i)
        if not match:
            continue
        info = match.groupdict()
        importlib.import_module("%s.%s" % (__name__, info["name"]))
    return MockCacheSchema.REGISTERED_SCHEMAS
