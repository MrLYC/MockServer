({
    schemas: {
        "HTTP": {
            "name": "HTTP",
            "schema": "mock_http",
            "activated": true,
            "fields": {
                "method": ["GET", "POST", "DELETE", "PUT", "PATCH", "HEAD"],
                "path": "string",
                "query_string": "string"
            }
        },
        "TCP": {
            "name": "TCP",
            "schema": "mock_tcp",
            "activated": false,
            "fields": {
                "request": "string"
            }
        }
    },
    schema_items: {
        "name": "HTTP",
        "items": {}
    },
    schema_data: {
        "name": "HTTP",
        "fields": {},
        "response": {}
    },
    init: function () {
        var nav_vm = new Vue({
            el: "#nav",
            data: this.schemas
        })
    }
}).init();
