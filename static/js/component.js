(function functionName() {
  Vue.component("mock-field", {
    template: "#component-mock-field",
    props: ["field", "model"],
    data: function () {
      return {
        old_xname: "",
        xname: "",
        xvalue: "",
        xfields: {},
      };
    },
    methods: {
      setValue: function (target) {
        if (target.value && this.field.pattern) {
          if (!target.value.match(this.field.pattern)) {
            this.$emit("mock-field-input-error", this);
            target.value = this.model[this.field.name];
            return;
          }
        }
        Vue.set(this.model, this.field.name, target.value);
      },
      setXValue: function () {
        if (!this.xname) {
          return;
        }
        var xname = this.field.name + ":" + this.xname;
        this.model[xname] = this.xvalue;
        this.xname = "";
        this.xvalue = "";
        Vue.set(this.xfields, xname, {
          name: xname,
          type: this.field.type,
          default: "",
          multiple: false,
        });
      },
      delXValue: function (xname) {
        Vue.delete(this.model, xname);
        Vue.delete(this.xfields, xname);
      }
    },
  });

  Vue.component("mock-details", {
    template: "#component-mock-details",
    props: ["schema", "model"],
    methods: {
      sorted_fields: function (fields) {
        var field_list = [];
        for (f in fields) {
          if (fields.hasOwnProperty(f)) {
            field_list.push(fields[f]);
          }
        }
        field_list.sort(function (x, y) {
          if (x.multiple != y.multiple) {
            if (x.multiple) {
              return 1;
            }
            else {
              return -1;
            }
          }
          if (x.rich_text != y.rich_text) {
            if (x.rich_text) {
              return 1;
            }
            else {
              return -1;
            }
          }
          if (x.type != y.type) {
            return x.type.localeCompare(y.type);
          }
          return x.name.localeCompare(y.name);
        });
        return field_list;
      }
    },
  });
})();
