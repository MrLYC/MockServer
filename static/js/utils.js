var MockServerUtils = new function() {
    var endpoint = this.endpoint = document.location.protocol + "//" + document.location.host + "/";
    var urlJoin = this.urlJoin = function(url, part, params) {
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
    };

    var alertMessage = this.alertMessage = function(message) {
        alert(message);
    };

    var Request = this.Request = function(success_callback, error_callback) {
        var self = this;
        self.success_callback = success_callback;
        self.error_callback = error_callback;
        self.request = new XMLHttpRequest();
        self.request.onload = function() {
            var request = self.request;
            if (
                success_callback &&
                request.status >= 200 &&
                request.status < 400
            ) {
                success_callback(request);
            } else if (error_callback) {
                error_callback(request);
            }
        };

        self.request.onerror = function() {
            if (error_callback) {
                error_callback(self.request);
            }
        };

        self.send = function(url, method, params, data, response_type, content_type) {
            var request = self.request;
            if (params) {
                url = urlJoin(url, "", params);
            }
            request.open(method, url, true);
            if (content_type) {
                request.setRequestHeader("Content-Type", content_type);
            }
            if (response_type) {
                request.responseType = response_type;
            }
            request.send(data);
        };

        self.get = function(url, params, response_type) {
            self.send(url, "GET", params, undefined, response_type);
        };

        self.post = function(url, params, data, response_type, content_type) {
            self.send(
                url, "POST", params, data, response_type, content_type
            );
        };

        self.del = function(url, params) {
            self.send(url, "DELETE", params);
        };

        self.postJson = function(url, data) {
            self.send(
                url, "POST", undefined, JSON.stringify(data),
                "json", "application/json"
            );
        };

        self.getJson = function(url, params) {
            self.send(url, "GET", params, undefined, "json");
        };

        self.getText = function(url, params) {
            self.send(url, "GET", params, undefined, "text");
        };
    };

    this.loadTemplate = function(url, success_callback, error_callback) {
        var error_callback = error_callback || function(request) {
            alertMessage(request.response);
        };
        var request = new MockServerUtils.Request(
            function(req) {
                success_callback(req.response);
            },
            error_callback
        );
        request.getText(url);
    }
};
