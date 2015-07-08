#!/usr/bin/env python
from util import *
from assertion import *
import re

class Validator(object):
    def __init__(self, spec, schema):
        self.spec = spec
        self.schema = schema


    def _is_node(self, key):
        return key.startswith("/")


    def _is_user_schema(self, key):
        return key.startswith("#")


    def _is_assertion(self, key):
        return key in ["contains",
                       "matches",
                       "file_exists",
                       "url_with_status_code_200"]

    def _is_user_schema_reference(self, method):
        return method.startswith("@") or method.startswith("#@")

    def _expand_user_schema_reference(self, ref):
        requesting_keys = False
        offset = 1
        if ref.startswith("#"):
            requesting_keys = True
            offset = 2

        ref = ref[offset:]
        obj = self.user_schema

        path = ref.split('/')
        for item in path:
            try:
                obj = obj[item]
            except:
                raise AssertionError("Invalid reference '%s'" % ref)

        if requesting_keys:
            return obj.keys()
        else:
            return obj



    def _assert_contains(self, expectation, value):
        try:
            assert_contains_only_fields(value, expectation.keys())
            for k, method in expectation.iteritems():
                self._do_assertion(method, None, value, k)
        except AssertionError, err:
            raise err


    def _do_assertion(self, method, expectation, value, key=None):
        if method == "contains":
            self._assert_contains(expectation, value)
        elif method == "non_empty_string":
            assert_non_empty_string(value, key)
        elif method == "non_empty_list":
            assert_non_empty_list(value, key)
        elif self._is_user_schema_reference(method):
           expectation = self._expand_user_schema_reference(method)
           assert_valid_artifact(value, key, expectation)
        else:
            raise ValueError("Not implemented %s" % method  + " " + str(value) + " " + key)


    def _create_recipe(self, schema, path="", recipe={}, user_schema={}):
        for k, v in schema.iteritems():
            if self._is_user_schema(k):
                user_schema[k[1:]] = v
            elif self._is_assertion(k):
                if not path in recipe:
                    recipe[path] = []
                recipe[path].append((k, v))
            elif self._is_node(k):
                self._create_recipe(v, path + k, recipe, user_schema)
            else:
                raise ValueError("Invalid key '%s' in schema at '%s'" % (k, path))
        return recipe, user_schema


    def _validate(self, value, recipe, path="/"):
        if len(recipe.keys()) == 0:
            return

        rule_path = path
        if rule_path in recipe:
            for assertion in recipe[rule_path]:
                method, expectation = assertion
                self._do_assertion(method, expectation, value)
        else:
            pass

        if isinstance(value, dict):
            for k, v in value.iteritems():
                if isinstance(v, dict) or isinstance(v, list):
                    next_path = path + "/" + k
                    self._validate(v, recipe, next_path)
        elif isinstance(value, list):
            for v in value:
                if isinstance(v, dict) or isinstance(v, list):
                    next_path = path + "/*"
                    self._validate(v, recipe, next_path)


    def validate(self, error_details=None):
       recipe = {}
       user_schema = {}
       self._create_recipe(self.schema,
                           path="",
                           recipe=recipe,
                           user_schema=user_schema)
       self.user_schema = user_schema
       self._validate(self.spec, recipe)



def main(args):
    spec = load_json(args.spec)
    schema = load_json(args.validation_schema)
    v = Validator(spec, schema)
    error_details = {}
    try:
        v.validate(error_details)
    except AssertionError, err:
        print 'ERROR:', err.message
        print json.dumps(error_details, indent=4)
        sys.exit(1)

if __name__ == "__main__":
    parser.add_argument('-s', '--spec', type = str, default = None,
        help = 'Specify a file used for describing and generating the tests')
    parser.add_argument('-v', '--validation_schema', type = str, default = None,
        help = 'Specify a file used for validating the specification')
    args = parser.parse_args()
    main(args)
