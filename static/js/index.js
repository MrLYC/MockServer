
function urlJoin(url, part, params) {
    var values = [];
    for (var k in params) {
        values.push(encodeURIComponent(k) + "=" + encodeURIComponent(params[k]));
    }
    if (part) {
        url = url + part;
    }
    if (values.length > 0) {
        url = url + "?" + values.join("&");
    }
    return url;
}

function alert_message(message) {
    alert(message);
}

function Request(success_callback, error_callback) {
    var self = this;
    self.success_callback = success_callback;
    self.error_callback = error_callback;
    self.request = new XMLHttpRequest();
    self.request.onload = function () {
        var request = self.request;
        if (success_callback && request.status >= 200 && request.status < 400) {
            success_callback(request);
        } else if (error_callback) {
            error_callback(request);
        }
    };

    self.request.onerror = function () {
        if (error_callback) {
            error_callback(self.request);
        }
    };

    self.del = function (url, params) {
        var request = self.request;
        request.open("DELETE", urlJoin(url, "", params), true);
        request.send();
    };

    self.postJson = function (url, data) {
        var request = self.request;
        request.open("POST", url, true);
        request.setRequestHeader("Content-Type", "application/json");
        request.responseType = "json";
        request.send(JSON.stringify(data));
    };

    self.getJson = function (url, params) {
        var request = self.request;
        request.responseType = "json";
        request.open("GET", urlJoin(url, "", params), true);
        request.send();
    };
}

function SchemaAPI(endpoint) {
    var self = this;
    self.url = urlJoin(endpoint, "api/schemas");
    self.get = function (schema, success_callback, error_callback) {
        var params = {};
        var request = new Request(success_callback, error_callback);
        if (schema) {
            params.schema = schema;
        }
        request.getJson(urlJoin(self.url, "", params));
    };
}

function ItemAPI(endpoint) {
    var self = this;
    self.url = urlJoin(endpoint, "api/items");

    self.get = function (uri, success_callback, error_callback) {
        var request = new Request(success_callback, error_callback);
        request.getJson(urlJoin(self.url, "", {uri: uri}));
    };

    self.post = function (uri, data, success_callback, error_callback) {
        var request = new Request(success_callback, error_callback);
        request.postJson(self.url, data);
    };

    self.parseUri = function (uri) {
        var re_sep = /[^:\/]+/g;
        var schema = re_sep.exec(uri)[0];
        var mathch = null;
        var fields = [];
        var items = {};
        var values = {};
        var strict = true;
        while (match = re_sep.exec(uri)) {
            var item = match[0].split("=", 2);
            var key = item[0];
            var value = item[1];
            fields.push(key);
            items[key] = value;
            if (key == "!" || value.startsWith("~")) {
                strict = false;
            }
            else {
                var buf = [];
                for (var i = 0; i < value.length; i += 2) {
                    buf.push(String.fromCharCode(
                        parseInt(value.substr(i, 2), 16)
                    ));
                }
                values[key] = buf.join("");
            }
        }
        return {
            schema: schema,
            strict: strict,
            fields: fields,
            values: values,
            items: items,
        };
    }
}

var endpoint = document.location.protocol + "//" + document.location.host + "/";

Vue.component('object-details', {
    template: '#object-details',
    props: ['self', 'name'],
});

var schema_tab_view = new Vue({
    el: "#schema-tab",
    data: {
        current_schema_name: null,
        schemas: {},
    },
    computed: {
        self: function () {
            return this;
        },
        schema: function () {
            return this.schemas[this.current_schema_name];
        },
    },
    methods: {
        init: function (default_name) {
            var self = this;
            var schema_api = new SchemaAPI(endpoint);
            schema_api.get("", function (request) {
                var response = request.response;
                if (!response.ok) {
                    alert_message(response.message);
                    return;
                }
                for (var schema of response.data) {
                    if (schema.schema == default_name) {
                        self.current_schema_name = schema.schema;
                    }
                    Vue.set(self.schemas, schema.schema, schema);
                }
            }, function (request) {
                    alert_message("server has gone");
            });
        },
    },
});

var item_list_view = new Vue({
    el: "#schema-list",
    data: {
        schema: null,
        item: null,
    },
    computed: {
        self: function () {
            return this;
        },
        items: function () {
            if (this.schema) {
                return this.schema.items;
            }
        }
    },
});

var item_detail_view = new Vue({
    el: "#item-details",
    data: {
        item: null,
        schema: null,
        request: {},
        response: {},
    },
    computed: {
        self: function () {
            return this;
        },
    },
});


var bridge = new Vue({
    el: "#bridge",
    data: {
        schema: null,
        item: null,
    },
    computed: {
        data: function () {
            return {
                schema: this.schema && this.schema.schema,
                request: this.request,
                response: this.response,
            };
        }
    },
    methods: {
        init: function () {
            schema_tab_view.init("mock_http");
            this.onSchemaChange(schema_tab_view.schema);
        },
        onSchemaChange: function (schema) {
            this.schema = schema;
            item_detail_view.schema = schema;
            item_list_view.schema = schema;
            if (schema_tab_view.current_schema_name != schema.schema) {
                schema_tab_view.current_schema_name = schema.schema;
            }
        },
        onItemChange: function (item, schema) {
            if (schema) {
                this.onSchemaChange(schema);
            }
            this.item = item;
            item_detail_view.item = item;
            item_list_view.item = item;
            this.request = {};
            this.response = {};
        },
        setItemUri: function (uri) {
            var api = new ItemAPI(endpoint);
            var self = this;
            api.get(uri, function (request) {
                var response = request.response;
                if (!response.ok) {
                    alert_message(response.message);
                    return;
                }
                if (response.data.length < 0) {
                    alert_message("uri not found: " + uri);
                    return;
                }
                self.onItemChange(response.data[0]);
            }, alert_message);
        },
    },
});
bridge.init();
