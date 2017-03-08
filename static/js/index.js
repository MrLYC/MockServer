
function urlJoin(url, part, params) {
    var values = [];
    for (k in params) {
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
    },
});
var item_list_view = new Vue({
    el: "#schema-list",
    data: {
        current_schema_name: null,
        items: {},
    },
    computed: {
        self: function () {
            return this;
        },
    },
});
var item_detail_view = new Vue({
    el: "#item-details",
    data: {
        current_schema_name: null,
        current_uri: null,
    },
    computed: {
        self: function () {
            return this;
        },
    },
});

var schema_api = new SchemaAPI(endpoint);
schema_api.get("", function (request) {
    var response = request.response;
    if (!response.ok) {
        console.log(response.message);
        return;
    }
    for (schema of response.data) {
        if (!schema_tab_view.current_schema_name) {
            schema_tab_view.current_schema_name = schema.name;
        }
        Vue.set(schema_tab_view.schemas, schema.name, schema);
    }
}, function (request) {
        alert("server has gone");
});
