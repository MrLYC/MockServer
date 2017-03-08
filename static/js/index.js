
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
        var request = new Request(success_callback, error_callback);
        request.getJson(urlJoin(self.url, "", {schema: schema}));
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
        request.getJson(self.url, data);
    };
    
    self.del = function (uri, success_callback, error_callback) {
        var request = new Request(success_callback, error_callback);
        request.del(urlJoin(self.url, "", {uri: uri}));
    };
}

