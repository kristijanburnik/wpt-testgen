#!/usr/bin/env python
from assertion import *
from util import *
import re, sys


class SchemaError(Exception):
    """Error raised when detected a schema problem."""
    pass


class SpecError(Exception):
    """Error raised when detected a schema violation in spec."""
    pass


class Validator(object):
    def __init__(self, spec, schema):
        self.spec = spec
        self.schema = schema


    def validate(self, error_details={}):
       self._meta_schema = {}
       self._rulemap = {}
       self._create_rulemap(self.schema, path="")
       self._validate(self.spec, self._rulemap, error_details=error_details)


    def _is_node(self, key):
        return key.startswith("/")


    def _is_meta_schema(self, key):
        return key.startswith("#")


    def _is_assertion(self, key):
        return key in ["matches", "has_keys", "each_value"]

    def _is_meta_schema_reference(self, method):
        return hasattr(method, 'startswith') and method.startswith("@")


    def _expand_meta_schema_reference(self, ref):
        if ref.startswith("#"):
            requesting_keys = True
            offset = 2
        else:
            requesting_keys = False
            offset = 1

        ref = ref[offset:]
        obj = self._meta_schema

        path = ref.split('/')
        for item in path:
            try:
                obj = obj[item]
            except:
                raise SchemaError("Invalid reference '%s'" % ref)

        if requesting_keys:
            return obj.keys()
        else:
            return obj


    def _assert_matches(self, expectation, value):
        if not isinstance(expectation, dict):
            raise SchemaError("Schema \"matches\" operator expects a dict " + \
                              "or schema reference, got '%s'" % expectation)

        assert_contains_only_fields(value, expectation.keys())
        for k, method in expectation.iteritems():
            self._do_assertion(method, None, value, k)


    def _assert_values(self, expectation, mixed):
        if isinstance(mixed, dict):
            keys = mixed
        elif isinstance(mixed, list):
            keys = range(0, len(mixed))

        for key in keys:
            self._do_assertion(expectation, None, mixed, key)


    def _do_assertion(self, method, expectation, value, key=None):
        if self._is_meta_schema_reference(expectation):
            expectation = self._expand_meta_schema_reference(expectation)

        try:
            if method == "matches":
                self._assert_matches(expectation, value)
            elif method == "has_keys":
                assert_contains_only_fields(value, expectation)
            elif method == "each_value":
                self._assert_values(expectation, value)
            elif method == "non_empty_string":
                assert_non_empty_string(value, key)
            elif method == "non_empty_list":
                assert_non_empty_list(value, key)
            elif method == "non_empty_dict":
                assert_non_empty_dict(value, key)
            elif method == "integer":
                assert_integer(value, key)
            elif method == "existing_file":
                assert_file_exists(value, key)
            elif self._is_meta_schema_reference(method):
               expectation = self._expand_meta_schema_reference(method)
               assert_valid_subset(value, key, expectation)
            elif isinstance(method, list):
                expectation = method
                assert_valid_subset(value, key, expectation)
            else:
                raise SchemaError('Non-existing assertion method "%s"' %
                                  method)
        except AssertionError, err:
            raise SpecError(err)

    def _create_rulemap(self, schema, path=""):
        if not isinstance(schema, dict):
            raise SpecError('Value at schema path "%s" must be a dict' % \
                            path)

        for k, v in schema.iteritems():
            if self._is_meta_schema(k):
                self._meta_schema[k[1:]] = v
            elif self._is_assertion(k):
                if not path in self._rulemap:
                    self._rulemap[path] = []
                self._rulemap[path].append((k, v))
            elif self._is_node(k):
                self._create_rulemap(v, path + k)
            else:
                raise SchemaError("Invalid key '%s' in schema at '%s'" % \
                                  (k, path))



    def _validate(self, value, rulemap, path="/", error_details={}):
        error_details["path"] = path
        error_details["value"] = value
        if len(rulemap.keys()) == 0 and path != "/":
            raise SpecError('No schema rule for path "%s"' % path)

        if path in rulemap:
            for assertion in rulemap[path]:
                method, expectation = assertion
                error_details["expectation"] = expectation
                self._do_assertion(method, expectation, value)

        if isinstance(value, dict):
            sequence = value.iteritems()
        elif isinstance(value, list):
            sequence = [("*", v) for v in value]
        else:
            raise SchemaError("Unexpected value: %s" % str(value))

        for k, v in sequence:
            if isinstance(v, dict) or isinstance(v, list):
                next_path = path + "/" + k
                self._validate(v, rulemap, next_path, error_details)


def main(args):
    spec = load_json(args.spec)
    schema = load_json(args.validation_schema)
    v = Validator(spec, schema)
    error_details = {}
    try:
        v.validate(error_details=error_details)
        return
    except SchemaError, err:
        print 'Schema Error:', err.message
    except SpecError, err:
        print 'Spec Error:', err.message
        print json.dumps(error_details, indent=2)

    sys.exit(1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='TestGen validation utility')
    parser.add_argument('-s', '--spec', type=str, required=True,
        help = 'Specification file used for describing and generating tests')
    parser.add_argument('-v', '--validation_schema', type=str, required=True,
        help = 'Validation file for validating the specification')
    args = parser.parse_args()
    main(args)
