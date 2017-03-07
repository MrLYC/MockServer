(function() {
    var FieldType = {
        string: "string",
        integer: "integer",
        boolean: "boolean",
        choice: "choice",
        extend: "extend",
        object: "object",
    };
 
    function Proxy(object, attributes) {
        var self = this;
        self.__proto__ = object;
        for(k in attributes) {
            self[k] = attributes[k];
        }
    }

    function Field(name, type, default_value, choices) {
        var self = this;
        self.name = name;
        self.type = type;
        self.default_value = default_value;
        self.choices = choices;
    }

    function ItemValue(field, value) {
        var self = this;
        self.field = field;
        self.value = value;
    }

    function UriItem(uri, request, response) {
        var self = this;
        self.uri = uri;
        self.request = request;
        self.response = response;
    }

    function Schema(name, schema, request_fields, response_fields) {
        var self = this;
        self.name = name;
        self.schema = schema;
        self.request_fields = request_fields;
        self.response_fields = response_fields;
    }

    var schemas = {
        HTTP: new Schema(
            "HTTP", "mock_http",
            [
                new Field("method", FieldType.choice, "GET", [
                    "GET", "POST", "PUT", "DELETE", "HEAD", "PATCH",
                ]),
                new Field("path", FieldType.string),
                new Field("query_string", FieldType.extend),
                new Field("http_header", FieldType.extend),
            ],
            [
                new Field("status_code", FieldType.integer, 200),
                new Field("status_reason", FieldType.string, "ok"),
                new Field("cookie", FieldType.object),
                new Field("header", FieldType.object),
                new Field("data_type", FieldType.choice, "raw", [
                    "static_file", "base64", "raw",
                ]),
            ]
        ),
        TCP: new Schema(
            "TCP", "mock_tcp",
            [
                new Field("request", FieldType.string),
            ],
            [
                new Field("greeting", FieldType.string),
                new Field("sep_regex", FieldType.string),
                new Field("data_type", FieldType.choice, "raw", [
                    "base64", "raw",
                ]),
                new Field("data", FieldType.string),
                new Field("close_stream", FieldType.boolean, false, [
                    true, false,
                ]),
            ]
        ),
    }
    
    vm = new Vue({
        el: "#main",
        data: {
            schemas: schemas,
            item: new UriItem(),
            x_schema: "HTTP",
            x_items: [],
        },
        computed: {
            schema: {
                get: function() {
                    return this.schemas[this.x_schema];
                },
                set: function(schema) {
                    this.x_schema = schema.name;
                    this.x_items = [];
                },
            },
            
        }
    });
})();
