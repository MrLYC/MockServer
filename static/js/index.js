(function() {
    function Request (success_callback, error_callback) {
        var self = this;
        self.success_callback = success_callback;
        self.error_callback = error_callback;
        self.request = new XMLHttpRequest();
        self.request.onload = function (){
            if (success_callback && self.status >= 200 && self.status < 400) {
                success_callback(self);
            }
            else if (error_callback) {
                error_callback(self);
            }
        }
        self.request.onerror = function () {
            if (error_callback) {
                error_callback(self);
            }
        }

        self.postJson = function (url, data) {
            var request = self.request;
            request.open("POST", url, true);
            request.setRequestHeader("Content-Type", "application/json");
            request.send(JSON.stringify(data));
        }

        self.getJson = function (url) {
            var request = self.request;
            request.open("GET", url, true);
            request.send();
        }
    }

    function SchemaAPI () {
        var self = this;
        self.url = "/schemas";
        self.get = function (schemas, success_callback, error_callback) {
            var query_string = []
            for (schema of schemas) {
                query_string.push("schema=" + schema);
            }
            var request = new Request(success_callback, error_callback);
            request.getJson(self.url + "?" + encodeURI(query_string.join("&")));
        }
    }
})();
