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

class NotReachedError(Exception):
    """Error raised when unreachable code is executed."""
    pass

class Validator(object):
    def __init__(self, spec, schema):
        self._rule_method = {"matches": self._assert_matches,
                             "has_keys": self._assert_has_keys,
                             "each_value": self._assert_each_value}
        self._assert_method = {"non_empty_string": assert_non_empty_string,
                               "non_empty_list": assert_non_empty_list,
                               "non_empty_dict": assert_non_empty_dict,
                               "integer": assert_integer,
                               "existing_file": assert_file_exists}
        self.spec = spec
        self.schema = schema

    def validate(self, error_details={}):
        self.meta_schema_map = {}
        self.leafs = {}
        self._meta_schema = {}
        self._rule_map = {}
        self._create_rule_map(self.schema, path="")

        # Flatten the rule map by path.
        # TODO(kristijanburnik): Refactor this extraction.
        for path, assertions in self._rule_map.iteritems():
            for assertion in assertions:
                rule, expectation = assertion

                if rule != "matches":
                    continue

                if self._is_meta_schema_reference(expectation):
                    expectation = self._expand_meta_schema_reference(expectation)

                for k, v in expectation.iteritems():
                    if self._is_meta_schema_reference(v):
                        valid_values = self._expand_meta_schema_reference(v)
                    elif isinstance(v, list):
                        valid_values = v
                    else:
                        continue

                    self.meta_schema_map[path + "/" + k] = valid_values

        self._validate(self.spec, self._rule_map, error_details=error_details)

    def _is_node(self, key):
        return key.startswith("/")

    def _is_meta_schema(self, key):
        return key.startswith("#")

    def _is_rule(self, key):
        return key in self._rule_method

    def _is_assertion(self, key):
        return key in self._assert_method

    def _is_meta_schema_reference(self, token):
        return hasattr(token, 'startswith') and token.startswith("@")

    def _get_meta_schema_name(self, token):
        return token[1:]

    def _expand_meta_schema_reference(self, token):
        meta_schema = self._meta_schema
        for subkey in self._get_meta_schema_name(token).split('/'):
            try:
                meta_schema = meta_schema[subkey]
            except:
                raise SchemaError("Invalid meta schema reference '%s'" % token)
        return meta_schema

    def _assert_matches(self, expectation, value):
        if not isinstance(expectation, dict):
            raise SchemaError("Schema rule \"matches\" expects a dict " + \
                              "or meta schema reference, got '%s'" % \
                              expectation)
        assert_contains_only_fields(value, expectation.keys())
        for key, method in expectation.iteritems():
            self._assert_spec_value(method, None, value, key)

    def _assert_each_value(self, expectation, mixed):
        if isinstance(mixed, dict):
            keys = mixed
        elif isinstance(mixed, list):
            keys = range(0, len(mixed))

        for key in keys:
            self._assert_spec_value(expectation, None, mixed, key)

    def _assert_has_keys(self, expectation, value):
        assert_contains_only_fields(value, expectation)

    def _assert_spec_value(self, method, expectation, value, key):
        if self._is_meta_schema_reference(method):
            expectation = self._expand_meta_schema_reference(method)
            assert_valid_subset(value, key, expectation)
        elif isinstance(method, list):
            expectation = method
            assert_valid_subset(value, key, expectation)
        elif self._is_assertion(method):
            assertion_method = self._assert_method[method]
            assertion_method(value, key)
        else:
            raise SchemaError('Non-existing assertion method "%s"' % method)

    def _validate_rule(self, rule, expectation, value):
        """Validates a node's left handside rule."""
        if self._is_meta_schema_reference(expectation):
            expectation = self._expand_meta_schema_reference(expectation)

        try:
            if rule in self._rule_method:
                rule_method = self._rule_method[rule]
                rule_method(expectation, value)
            else:
                raise NotReachedError(rule)
        except AssertionError, err:
            raise SpecError(err)

    def _create_rule_map(self, schema, path=""):
        if not isinstance(schema, dict):
            raise SpecError('Value at schema path "%s" must be a dict' % \
                            path)

        for k, v in schema.iteritems():
            if self._is_meta_schema(k):
                self._meta_schema[self._get_meta_schema_name(k)] = v
            elif self._is_rule(k):
                if not path in self._rule_map:
                    self._rule_map[path] = []
                self._rule_map[path].append((k, v))
            elif self._is_node(k):
                self._create_rule_map(v, path + k)
            # TODO(kristijanburnik): Refactor leaf detection.
            elif k == "path":
                if not path in self.leafs:
                    self.leafs[path] = [None, None]
                self.leafs[path][0] = v
            elif k == "template":
                if not path in self.leafs:
                    self.leafs[path] = [None, None]
                self.leafs[path][1] = v
            else:
                raise SchemaError('Invalid schema rule "%s" at "%s"' % \
                                  (k, path))

    def _validate(self, value, rule_map, path="/", error_details={}):
        error_details["path"] = path
        error_details["value"] = value
        if len(rule_map.keys()) == 0 and path != "/":
            raise SpecError('No schema rule for path "%s"' % path)

        if path in rule_map:
            for assertion in rule_map[path]:
                rule, expectation = assertion
                error_details["expectation"] = expectation
                self._validate_rule(rule, expectation, value)

        if isinstance(value, dict):
            sequence = value.iteritems()
        elif isinstance(value, list):
            sequence = [("*", v) for v in value]
        else:
            raise SchemaError("Unexpected value: %s" % str(value))

        for k, v in sequence:
            if isinstance(v, dict) or isinstance(v, list):
                next_path = path + "/" + k
                self._validate(v, rule_map, next_path, error_details)


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
    #TODO(kristijanburnik). Merge as common options.
    parser.add_argument('-s', '--spec', type=str, required=True,
        help = 'Specification file used for describing and generating tests')
    parser.add_argument('-v', '--validation_schema', type=str, required=True,
        help = 'Validation file for validating the specification')
    args = parser.parse_args()
    main(args)
