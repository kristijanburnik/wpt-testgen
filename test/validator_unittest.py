import test_includes
import unittest
import validator


class ValidatorTestCase(unittest.TestCase):
    def assert_valid(self, spec, schema):
        try:
            v = validator.Validator(spec, schema)
            v.validate()
        except AssertionError, err:
            self.fail(err)


    def assert_invalid(self, spec, schema, message=None):
        try:
            v = validator.Validator(spec, schema)
            v.validate()
        except AssertionError, err:
            self.assertEqual(message, str(err))
            return

        self.fail("Expected failed validation.")


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
        self.assert_invalid(spec, schema,
                            'List "specification" must not be empty')


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


    def test_level2InvalidSpecEmptyString_fails(self):
        spec = {"specification" : [{"name": "Sample1"},
                                   {"name": ""}]}
        schema = {"/" : {
            "matches": {"specification": "non_empty_list"},
            "/specification": {
                "/*": {"matches": {"name": "non_empty_string"}}
            }
        }}
        self.assert_invalid(spec, schema,
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
        self.assert_invalid(spec, schema,
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
        self.assert_invalid(spec, schema,
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
        self.assert_invalid(spec, schema,
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
        self.assert_invalid(spec, schema,
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
        self.assert_invalid(spec, schema,
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
        self.assert_invalid(spec, schema,
                            "Invalid reference 'schema/non_subrule'")


    def test_validSpecGoodRef_passes(self):
        spec = {"specification" : ["one"]}
        schema = {"/" : {
            "matches": {"specification": "@schema/subrule"},
            "#schema": {"subrule": ["one", "two", "three"]}
        }}
        self.assert_valid(spec, schema)


    def test_validSpecWithSchemaReference_Passes(self):
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


    def test_invalidSpecWithSchemaReferenceBadFruit_Fails(self):
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
        self.assert_invalid(spec, schema,
                            'Field "fruit" must be from: ' + \
                            '[\'*\', \'apple\', \'lemon\', \'orange\']')


    def test_invalidSpecWithSchemaReferenceEmptyName_Fails(self):
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
        self.assert_invalid(spec, schema,
                            'Field "name" must not be empty')


    def test_invalidSpecWithSchemaReferenceExtraMember_Fails(self):
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
        self.assert_invalid(spec, schema,
                            'Unexpected field "not-in-spec".')


    def test_missingSchemaRule_Fails(self):
        spec = {"myspec": []}
        schema = {}
        self.assert_invalid(spec, schema,
                            'No schema rule for path "//myspec"')


    def test_invalidSchemaNode_Fails(self):
        spec = {"myspec": []}
        schema = {"/": {
                    "/myspec": "non_empty_list"
                  }}
        self.assert_invalid(spec, schema,
                            'Value at schema path "//myspec" must be a dict')

    def test_invalidMatchesParameter_Fails(self):
        spec = {"myspec": []}
        schema = {"/": {
                    "/myspec": {"matches": "string_is_bad_here"}
                  }}
        self.assert_invalid(spec, schema,
                            'Schema "matches" operator expects a dict or ' + \
                            'schema reference, got \'string_is_bad_here\'')

    def test_NonExistingAssertion_Fails(self):
        spec = {"myspec": []}
        schema = {"/": {
                    "matches": {"myspec": "something_new"}
                  }}
        self.assert_invalid(spec, schema,
                            'Non-existing assertion method "something_new"')


    def test_allSupportedSchemaTypes_Passes(self):
        import os
        spec = {"spec": {
            "name": "valid-name",
            "items": [1, 2, 3],
            "subset": [2, 4, 8],
            "size_ratios": {"sun": 109, "earth": 1},
            "script": os.path.realpath(__file__)
        }}
        schema = {"/": {
                    "matches": {"spec": "non_empty_dict"},
                    "/spec": {
                        "matches": {
                            "name": "non_empty_string",
                            "items": "non_empty_list",
                            "subset": [1, 2, 4, 8, 16],
                            "size_ratios": "non_empty_dict",
                            "script": "existing_file"
                        },
                        "/size_ratios": {
                            "matches": {"sun": "integer",
                                        "earth": "integer"}
                        }
                    }
                  }}
        self.assert_valid(spec, schema)

if __name__ == '__main__':
    unittest.main()
