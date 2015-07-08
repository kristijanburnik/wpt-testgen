import test_includes
import unittest
import validator

#TODO(kristijanburnik): Add assertions of error types.

class ValidatorTestCase(unittest.TestCase):
    def assert_valid(self, spec, schema):
        try:
            v = validator.Validator(spec, schema)
            v.validate()
        except AssertionError, err:
            self.fail(err)

    def assert_invalid(self, spec, schema):
        try:
            v = validator.Validator(spec, schema)
            v.validate()
        except AssertionError, err:
            return

        self.fail("Expected failed validation.")

    def test_emptySpecAndSchema_passes(self):
        spec = {}
        schema = {}
        self.assert_valid(spec, schema)

    def test_simpleValidSpec_passes(self):
        spec = {"specification" : [{"name": "Sample1"},
                                   {"name": "Sample2"}]}
        schema = {"/" : {
            "contains": {"specification": "non_empty_list"}
        }}
        self.assert_valid(spec, schema)

    def test_simpleInvalidSpec_fails(self):
        spec = {"specification" : []}
        schema = {"/" : {
            "contains": {"specification": "non_empty_list"}
        }}
        self.assert_invalid(spec, schema)

    def test_level2ValidSpec_passes(self):
        spec = {"specification" : [{"name": "Sample1"},
                                   {"name": "Sample2"}]}
        schema = {"/" : {
            "contains": {"specification": "non_empty_list"},
            "/specification": {
                "/*": {"contains": {"name": "non_empty_string"}}
            }
        }}
        self.assert_valid(spec, schema)

    def test_level2InvalidSpecEmptyString_fails(self):
        spec = {"specification" : [{"name": "Sample1"},
                                   {"name": ""}]}
        schema = {"/" : {
            "contains": {"specification": "non_empty_list"},
            "/specification": {
                "/*": {"contains": {"name": "non_empty_string"}}
            }
        }}
        self.assert_invalid(spec, schema)

    def test_level2InvalidSpecBadType_fails(self):
        spec = {"specification" : [{"name": "Sample1"},
                                   {"name":  []}]}
        schema = {"/" : {
            "contains": {"specification": "non_empty_list"},
            "/specification": {
                "/*": {"contains": {"name": "non_empty_string"}}
            }
        }}
        self.assert_invalid(spec, schema)

    def test_level2InvalidSpecMissingMember_fails(self):
        spec = {"specification" : [{"name": "Sample1"},
                                   {}]}
        schema = {"/" : {
            "contains": {"specification": "non_empty_list"},
            "/specification": {
                "/*": {"contains": {"name": "non_empty_string"}}
            }
        }}
        self.assert_invalid(spec, schema)

    def test_level2InvalidSpecNonMember_fails(self):
        spec = {"specification" : [{"name": "Sample1"},
                                   {"nonmember":[]}]}
        schema = {"/" : {
            "contains": {"specification": "non_empty_list"},
            "/specification": {
                "/*": {"contains": {"name": "non_empty_string"}}
            }
        }}
        self.assert_invalid(spec, schema)

    def test_level2InvalidExcessiveNonMember_fails(self):
        spec = {"specification" : [{"name": "Sample1"},
                                   {"name": "Sample2", "nonmember": []}]}
        schema = {"/" : {
            "contains": {"specification": "non_empty_list"},
            "/specification": {
                "/*": {"contains": {"name": "non_empty_string"}}
            }
        }}
        self.assert_invalid(spec, schema)


    def test_validSpecWithUserSchema_passes(self):
        spec = {"specification" : [{"name": "Sample1",
                                    "color": "blue"}]}
        schema = {"/" : {
            "contains": {"specification": "non_empty_list"},
            "#color_schema": ["red", "green", "blue"],
            "/specification": {
                "/*": {
                    "contains": {"name": "non_empty_string",
                                 "color": "@color_schema"}
                }
            }
        }}
        self.assert_valid(spec, schema)


    def test_validSpecWithUserSchemaAndList_passes(self):
        spec = {"specification" : [{"name": "Sample1",
                                    "color": ["blue", "green"]}]}
        schema = {"/" : {
            "contains": {"specification": "non_empty_list"},
            "#color_schema": ["red", "green", "blue"],
            "/specification": {
                "/*": {
                    "contains": {"name": "non_empty_string",
                                 "color": "@color_schema"}
                }
            }
        }}
        self.assert_valid(spec, schema)


    def test_invalidSpecWithUserSchemaAndList_fails(self):
        spec = {"specification" : [{"name": "Sample1",
                                    "color": ["blue", "white"]}]}
        schema = {"/" : {
            "contains": {"specification": "non_empty_list"},
            "#color_schema": ["red", "green", "blue"],
            "/specification": {
                "/*": {
                    "contains": {"name": "non_empty_string",
                                 "color": "@color_schema"}
                }
            }
        }}
        self.assert_invalid(spec, schema)


    def test_validSpecWithUserSchemaAndWildcard_passes(self):
        spec = {"specification" : [{"name": "Sample1",
                                    "color": "*"}]}
        schema = {"/" : {
            "contains": {"specification": "non_empty_list"},
            "#color_schema": ["red", "green", "blue"],
            "/specification": {
                "/*": {
                    "contains": {"name": "non_empty_string",
                                 "color": "@color_schema"}
                }
            }
        }}
        self.assert_valid(spec, schema)

    def test_validSpecWithUserSchemaAndEmptyList_passes(self):
        spec = {"specification" : [{"name": "Sample1",
                                    "color": []}]}
        schema = {"/" : {
            "contains": {"specification": "non_empty_list"},
            "#color_schema": ["red", "green", "blue"],
            "/specification": {
                "/*": {
                    "contains": {"name": "non_empty_string",
                                 "color": "@color_schema"}
                }
            }
        }}
        self.assert_valid(spec, schema)


if __name__ == '__main__':
    unittest.main()
