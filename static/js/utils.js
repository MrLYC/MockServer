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
    }

    var alertMessage = this.alertMessage = function(message) {
        alert(message);
    }

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

        self.del = function(url, params) {
            var request = self.request;
            request.open("DELETE", urlJoin(url, "", params), true);
            request.send();
        };

        self.postJson = function(url, data) {
            var request = self.request;
            request.open("POST", url, true);
            request.setRequestHeader("Content-Type", "application/json");
            request.responseType = "json";
            request.send(JSON.stringify(data));
        };

        self.getJson = function(url, params) {
            var request = self.request;
            request.responseType = "json";
            request.open("GET", urlJoin(url, "", params), true);
            request.send();
        };
    }
};
