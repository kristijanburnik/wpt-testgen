import test_includes
import unittest
import validator
from validator import SchemaError, SpecError

class ValidatorTestCase(unittest.TestCase):
    def assert_valid(self, spec, schema):
        try:
            v = validator.Validator(spec, schema)
            v.validate()
            return v
        except SpecError, err:
            self.fail(err)

    def assert_invalid(self, spec, schema, expected_error_type,
                       expected_message):
        try:
            v = validator.Validator(spec, schema)
            v.validate()
            self.fail("Expected failed validation.")
            return
        except SpecError, err:
            self.assertTrue(expected_error_type is SpecError,
                            "Error type should be SpecError")
        except SchemaError, err:
            self.assertTrue(expected_error_type is SchemaError,
                            "Error type should be SchemaError")
        self.assertEqual(expected_message, str(err))

    def createExampleSchema(self):
        return {"/": {
            "matches": {"specification": "non_empty_list"},
            "/specification": {
                "/*": {
                "matches": {"name": "non_empty_string",
                            "juices": "non_empty_list"},
                "/juices": {
                    "/*": {"matches": "@juice_schema"}}}
            }},
            "#juice_schema": {
                "name": "non_empty_string",
                "color": ["red", "green", "blue"],
                "fruit": ["apple", "lemon", "orange"]}}

    def test_emptySpecAndSchema_passes(self):
        spec = {}
        schema = {}
        self.assert_valid(spec, schema)

    def test_simpleValidSpec_passes(self):
        spec = {"specification" : [{"name": "Sample1"},
                                   {"name": "Sample2"}]}
        schema = {"/" : {
            "matches": {"specification": "non_empty_list"}
        }}
        self.assert_valid(spec, schema)

    def test_simpleInvalidSpec_fails(self):
        spec = {"specification" : []}
        schema = {"/" : {
            "matches": {"specification": "non_empty_list"}
        }}
        self.assert_invalid(spec, schema, SpecError,
                            'List "specification" must not be empty')
    def test_simpleInvalidSchemaRule_fails(self):
        spec = {"specification" : []}
        schema = {"/" : {
            "not_a_rule": {"specification": "non_empty_list"}
        }}
        self.assert_invalid(spec, schema, SchemaError,
                            'Invalid schema rule "not_a_rule" at "/"')

    def test_level2ValidSpec_passes(self):
        spec = {"specification" : [{"name": "Sample1"},
                                   {"name": "Sample2"}]}
        schema = {"/" : {
            "matches": {"specification": "non_empty_list"},
            "/specification": {
                "/*": {"matches": {"name": "non_empty_string"}}
            }
        }}
        self.assert_valid(spec, schema)

    def test_level2ValidSpecWithLeafs_passes(self):
        spec = {"specification" : [{"name": "Sample1"},
                                   {"name": "Sample2"}]}
        schema = {"/" : {
            "matches": {"specification": "non_empty_list"},
            "/specification": {
                "/*": {
                    "matches": {"name": "non_empty_string"},
                    "action": "include",
                    "path": "%(name)s",
                    "template": "Hello, %(name)s"
                }
            }
        }}
        validator = self.assert_valid(spec, schema)
        self.assertEquals(validator.leafs["//specification/*"],
                          {"path": "%(name)s",
                           "template": "Hello, %(name)s",
                           "action": "include"})

    def test_level2InvalidSpecEmptyString_fails(self):
        spec = {"specification" : [{"name": "Sample1"},
                                   {"name": ""}]}
        schema = {"/" : {
            "matches": {"specification": "non_empty_list"},
            "/specification": {
                "/*": {"matches": {"name": "non_empty_string"}}
            }
        }}
        self.assert_invalid(spec, schema, SpecError,
                            'Field "name" must not be empty')

    def test_level2InvalidSpecBadType_fails(self):
        spec = {"specification" : [{"name": "Sample1"},
                                   {"name":  []}]}
        schema = {"/" : {
            "matches": {"specification": "non_empty_list"},
            "/specification": {
                "/*": {"matches": {"name": "non_empty_string"}}
            }
        }}
        self.assert_invalid(spec, schema, SpecError,
                            'Field "name" must be a string')

    def test_level2InvalidSpecMissingMember_fails(self):
        spec = {"specification" : [{"name": "Sample1"},
                                   {}]}
        schema = {"/" : {
            "matches": {"specification": "non_empty_list"},
            "/specification": {
                "/*": {"matches": {"name": "non_empty_string"}}
            }
        }}
        self.assert_invalid(spec, schema, SpecError,
                            'Must contain field "name"')

    def test_level2InvalidSpecNonMember_fails(self):
        spec = {"specification" : [{"name": "Sample1"},
                                   {"nonmember":[]}]}
        schema = {"/" : {
            "matches": {"specification": "non_empty_list"},
            "/specification": {
                "/*": {"matches": {"name": "non_empty_string"}}
            }
        }}
        self.assert_invalid(spec, schema, SpecError,
                            'Must contain field "name"')

    def test_level2InvalidExtraMember_fails(self):
        spec = {"specification" : [{"name": "Sample1"},
                                   {"name": "Sample2", "nonmember": []}]}
        schema = {"/" : {
            "matches": {"specification": "non_empty_list"},
            "/specification": {
                "/*": {"matches": {"name": "non_empty_string"}}
            }
        }}
        self.assert_invalid(spec, schema, SpecError,
                            'Unexpected field "nonmember".')

    def test_validSpecWithUserSchema_passes(self):
        spec = {"specification" : [{"name": "Sample1",
                                    "color": "blue"}]}
        schema = {"/" : {
            "matches": {"specification": "non_empty_list"},
            "#color_schema": ["red", "green", "blue"],
            "/specification": {
                "/*": {
                    "matches": {"name": "non_empty_string",
                                "color": "@color_schema"}
                }
            }
        }}
        self.assert_valid(spec, schema)

    def test_validSpecWithUserSchemaAndList_passes(self):
        spec = {"specification" : [{"name": "Sample1",
                                    "color": ["blue", "green"]}]}
        schema = {"/" : {
            "matches": {"specification": "non_empty_list"},
            "#color_schema": ["red", "green", "blue"],
            "/specification": {
                "/*": {
                    "matches": {"name": "non_empty_string",
                                "color": "@color_schema"}
                }
            }
        }}
        self.assert_valid(spec, schema)

    def test_invalidSpecWithUserSchemaAndList_fails(self):
        spec = {"specification" : [{"name": "Sample1",
                                    "color": ["blue", "white"]}]}
        schema = {"/" : {
            "matches": {"specification": "non_empty_list"},
            "#color_schema": ["red", "green", "blue"],
            "/specification": {
                "/*": {
                    "matches": {"name": "non_empty_string",
                                 "color": "@color_schema"}
                }
            }
        }}
        self.assert_invalid(spec, schema, SpecError,
                            'Field "color" must be from: ' + \
                            '[\'*\', \'red\', \'green\', \'blue\']')

    def test_validSpecWithUserSchemaAndWildcard_passes(self):
        spec = {"specification" : [{"name": "Sample1",
                                    "color": "*"}]}
        schema = {"/" : {
            "matches": {"specification": "non_empty_list"},
            "#color_schema": ["red", "green", "blue"],
            "/specification": {
                "/*": {
                    "matches": {"name": "non_empty_string",
                                "color": "@color_schema"}
                }
            }
        }}
        self.assert_valid(spec, schema)

    def test_validSpecWithUserSchemaAndEmptyList_passes(self):
        spec = {"specification" : [{"name": "Sample1",
                                    "color": []}]}
        schema = {"/" : {
            "matches": {"specification": "non_empty_list"},
            "#color_schema": ["red", "green", "blue"],
            "/specification": {
                "/*": {
                    "matches": {"name": "non_empty_string",
                                "color": "@color_schema"}
                }
            }
        }}
        self.assert_valid(spec, schema)

    def test_invalidSpecBadRef_fails(self):
        spec = {"specification" : ["one"]}
        schema = {"/" : {
            "matches": {"specification": "@schema/non_subrule"},
            "#schema": {"subrule": ["one", "two", "three"]}
        }}
        self.assert_invalid(spec, schema, SchemaError,
                            "Invalid meta schema reference " + \
                            "'@schema/non_subrule'")

    def test_validSpecGoodRef_passes(self):
        spec = {"specification" : ["one"]}
        schema = {"/" : {
            "matches": {"specification": "@schema/subrule"},
            "#schema": {"subrule": ["one", "two", "three"]}
        }}
        self.assert_valid(spec, schema)

    def test_validSpecWithSchemaReference_passes(self):
        spec = {
            "specification": [{
                "name": "example-spec",
                "juices": [
                    {
                        "name": "lemonade",
                        "color": ["red", "green"],
                        "fruit": "lemon"
                    }]}]
        }
        schema = self.createExampleSchema()
        self.assert_valid(spec, schema)

    def test_invalidSpecWithSchemaReferenceBadFruit_fails(self):
        spec = {
            "specification": [{
                "name": "example-spec",
                "juices": [
                    {
                        "name": "lemonade",
                        "color": ["red", "green"],
                        "fruit": "blueberry"
                    }]}]
        }
        schema = self.createExampleSchema()
        self.assert_invalid(spec, schema, SpecError,
                            'Field "fruit" must be from: ' + \
                            '[\'*\', \'apple\', \'lemon\', \'orange\']')

    def test_invalidSpecWithSchemaReferenceEmptyName_fails(self):
        spec = {
            "specification": [{
                "name": "example-spec",
                "juices": [
                    {
                        "name": "",
                        "color": ["red", "green"],
                        "fruit": "lemon"
                    }]}]
        }
        schema = self.createExampleSchema()
        self.assert_invalid(spec, schema, SpecError,
                            'Field "name" must not be empty')

    def test_invalidSpecWithSchemaReferenceExtraMember_fails(self):
        spec = {
            "specification": [{
                "name": "example-spec",
                "juices": [
                    {
                        "name": "lemonade",
                        "color": ["red", "green"],
                        "fruit": "lemon",
                        "not-in-spec": True
                    }]}]
        }
        schema = self.createExampleSchema()
        self.assert_invalid(spec, schema, SpecError,
                            'Unexpected field "not-in-spec".')

    def test_missingSchemaRule_fails(self):
        spec = {"myspec": []}
        schema = {}
        self.assert_invalid(spec, schema, SpecError,
                            'No schema rule for path "//myspec"')

    def test_invalidSchemaNode_fails(self):
        spec = {"myspec": []}
        schema = {"/": {
                    "/myspec": "non_empty_list"
                  }}
        self.assert_invalid(spec, schema, SpecError,
                            'Value at schema path "//myspec" must be a dict')
    def test_invalidMatchesParameter_fails(self):
        spec = {"myspec": []}
        schema = {"/": {
                    "/myspec": {"matches": "string_is_bad_here"}
                  }}
        self.assert_invalid(spec, schema, SchemaError,
                            'Schema rule "matches" expects a dict or ' + \
                            'meta schema reference, got \'string_is_bad_here\'')
    def test_NonExistingAssertion_fails(self):
        spec = {"myspec": []}
        schema = {"/": {
                    "matches": {"myspec": "something_new"}
                  }}
        self.assert_invalid(spec, schema, SchemaError,
                            'Non-existing assertion method "something_new"')

    def test_allSupportedSchemaTypes_passes(self):
        import os
        spec = {"spec": {
            "name": "valid-name",
            "items": [1, 2, 3],
            "subset": [2, 4, 8],
            "size_ratios": {"sun": 109, "earth": 1},
            "script": os.path.realpath(__file__),
            "key_mapper": {"a": "A", "b": "B"},
            "key_mapper2": {"a": "A", "b": "B"},
            "nonable_choice": None,
            "nonable_choice2": [None],
            "combined_file_map": {
                "a": os.path.realpath(__file__),
                "b": os.path.realpath(__file__)
            },
            "file_list": [
                os.path.realpath(__file__),
                os.path.realpath(__file__)
            ]
        }}
        schema = {"/": {
                    "matches": {"spec": "non_empty_dict"},
                    "/spec": {
                        "matches": {
                            "name": "non_empty_string",
                            "items": "non_empty_list",
                            "subset": [1, 2, 4, 8, 16],
                            "size_ratios": "non_empty_dict",
                            "script": "existing_file",
                            "key_mapper": "non_empty_dict",
                            "key_mapper2": "non_empty_dict",
                            "nonable_choice": [None, 1, 2],
                            "nonable_choice2": [None, 1, 2],
                            "combined_file_map": "non_empty_dict",
                            "file_list": "non_empty_list"
                        },
                        "/size_ratios": {
                            "matches": {"sun": "integer",
                                        "earth": "integer"}
                        },
                        "/key_mapper": {
                            "has_keys": ["a", "b"]
                        },
                        "/key_mapper2": {
                            "has_keys": "@mapper_keys"
                        },
                        "/combined_file_map": {
                            "has_keys": "@mapper_keys",
                            "each_value": "existing_file"
                        },
                        "/file_list": {
                            "each_value": "existing_file"
                        }
                    }
                  },
                 "#mapper_keys": ["a", "b"]}
        self.assert_valid(spec, schema)

if __name__ == '__main__':
    unittest.main()
