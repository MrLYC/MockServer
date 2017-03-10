var API = new function() {
    this.SchemaAPI = function(endpoint) {
        var self = this;
        self.url = MockServerUtils.urlJoin(endpoint || "", "api/schemas");
        self.get = function(schema, success_callback, error_callback) {
            var params = {};
            var request = new MockServerUtils.Request(success_callback, error_callback);
            if (schema) {
                params.schema = schema;
            }
            request.getJson(MockServerUtils.urlJoin(self.url, "", params));
        };
    }

    this.ItemAPI = function(endpoint) {
        var self = this;
        self.url = MockServerUtils.urlJoin(endpoint || "", "api/items");

        self.get = function(uri, success_callback, error_callback) {
            var request = new MockServerUtils.Request(success_callback, error_callback);
            request.getJson(MockServerUtils.urlJoin(self.url, "", {
                uri: uri,
            }));
        };

        self.post = function(uri, data, success_callback, error_callback) {
            var request = new MockServerUtils.Request(success_callback, error_callback);
            request.postJson(self.url, data);
        };

        self.parseUri = function(uri) {
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
                } else {
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
};
