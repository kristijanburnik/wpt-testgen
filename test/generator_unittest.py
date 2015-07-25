import test_includes
import unittest
import generator

class MockWriter(object):
    def __init__(self):
        self.fs = {}

    def write(self, filename, content):
        self.fs[filename] = content

class GeneratorTestCase(unittest.TestCase):

    def __test_simple_generatesSelection(self):
        spec = {
            "specification": [
                {
                    "name": "citrus",
                    "description": "the family Rutaceae.",
                    "test_expansion": [
                        {
                            "__comment__": "Oranges, oranges everywhere.",
                            "name": "orange",
                            "color": "*",
                            "expectation": "sweet"
                        },
                        {
                            "__comment__": "Squeeze me a lemonde.",
                            "name": "lemon",
                            "color": "*",
                            "expectation": "sour"
                        },
                    ]
                },
                {
                    "name": "roses",
                    "description": "the rose-type tree fruits.",
                    "test_expansion": [
                        {
                            "__comment__": "Pears are cool.",
                            "name": "pear",
                            "color": "*",
                            "expectation": "sweet"
                        },
                        {
                            "__comment__": "Apples are fine.",
                            "name": "apple",
                            "color": ["red", "green"],
                            "expectation": "sweet"
                        },
                    ]
                },
            ],
            "excluded_tests": [
                {
                    "__comment__": "Green and red lemons are a no-go.",
                    "name": "lemon",
                    "color": ["green", "red"],
                    "expectation": "*"
                },
                {
                    "__comment__": "I don't eat green oranges.",
                    "name": "orange",
                    "color": "green",
                    "expectation": "*"
                }
            ]
        }

        schema = {
            "/": {
                "matches": {"specification": "non_empty_list",
                            "excluded_tests": "non_empty_list"},
                "/specification/*": {
                    "matches": {
                        "name": "non_empty_string",
                        "description": "non_empty_string",
                        "test_expansion": "non_empty_list",
                    },
                    "/test_expansion/*": {
                        "path": "%(_name)s/%(color)s-%(name)s.html",
                        "template": "%(color)s %(name)s is of %(_description)s",
                        "action": "generate",
                        "matches": "@scenario_schema",
                        "when": [{
                            "match_any": [["%(color)s", "yellow"]],
                            "do": [{
                              "action": "generate",
                              "path": "%(_name)s/%(color)s-%(name)s.html.headers",
                              "template": "Sample-Header: %(color)s %(name)s"
                            }]
                          }]
                    }
                },
                "/excluded_tests/*": {
                    "action": "suppress",
                    "matches": "@scenario_schema"
                }
            },
            "#color_schema": ["red", "green", "yellow"],
            "#scenario_schema": {
                "name": "non_empty_string",
                "color": "@color_schema",
                "expectation": "@expectation_schema"
            },
            "#expectation_schema": ["sour", "sweet"]
        }

        g = generator.Generator(spec, schema, writer=MockWriter())
        g.generate()

        expected = [('roses/green-pear.html',
                     'green pear is of the rose-type tree fruits.'),
                    ('citrus/yellow-lemon.html',
                     'yellow lemon is of the family Rutaceae.'),
                    ('citrus/yellow-lemon.html.headers',
                     'Sample-Header: yellow lemon'),
                    ('roses/green-apple.html',
                     'green apple is of the rose-type tree fruits.'),
                    ('citrus/yellow-orange.html',
                     'yellow orange is of the family Rutaceae.'),
                    ('citrus/yellow-orange.html.headers',
                     'Sample-Header: yellow orange'),
                    ('citrus/red-orange.html',
                     'red orange is of the family Rutaceae.'),
                    ('roses/red-pear.html',
                     'red pear is of the rose-type tree fruits.'),
                    ('roses/red-apple.html',
                     'red apple is of the rose-type tree fruits.'),
                    ('roses/yellow-pear.html',
                     'yellow pear is of the rose-type tree fruits.'),
                    ('roses/yellow-pear.html.headers',
                     'Sample-Header: yellow pear')]

        self.assert_generated(expected, g.writer.fs)

    def test_comments(self):
        spec = {
          "scenarios": [
            {
              "name": "allowed-when-feature-not-enabled",
              "description": "All navigations allowed if feature is disabled.",
              "feature_enabled": "no",
              "url": "*",
              "expectation": "allowed"
            },
            {
              "name": "blocked-when-feature-enabled",
              "description": "Unsafe URLs blocked when feature is enabled",
              "feature_enabled": "yes",
              "url": "http://unsafe.url",
              "expectation": "blocked"
            },
            {
              "name": "allowed-when-feature-enabled",
              "description": "Safe URLs allowed when feature is enabled",
              "feature_enabled": "yes",
              "url": ["https://safe.url", "http://safe.url"],
              "expectation": "allowed"
            }
          ],
          "skip": [
             {
              "name": "Temporarily ignore allowed.",
              "description": "n/a",
              "feature_enabled": "*",
              "url": "*",
              "expectation": "allowed"
            }
          ]
        }

        schema = {
          "/scenarios/*": {
            "matches": "@scenario_schema",
            "action": "generate",
            "path": "%(expectation)s/%(__index__)s.html",
            "template": "%(name)s; %(feature_enabled)s; %(url)s; %(expectation)s;",
            "when": [{
              "match_any": [["%(feature_enabled)s", "yes"]],
              "do": [{
                "action": "generate",
                "path": "%(expectation)s/%(__index__)s.html.headers",
                "template": "Enable-Navigation-Blocking: allowed-url http://safe.url https://safe.url"
              }]
            }]
          },
          "/skip/*": {
              "matches": "@scenario_schema",
              "action": "suppress"
          },
          "#scenario_schema": {
            "name": "non_empty_string",
            "description": "non_empty_string",
            "feature_enabled": ["no", "yes"],
            "url": "@url_schema",
            "expectation": ["allowed", "blocked"]
          },
          "#url_schema": ["http://safe.url", "https://safe.url", "http://unsafe.url"]
        }

        g = generator.Generator(spec, schema, writer=MockWriter())
        g.generate()

        expected = [('blocked/3.html',
                     'blocked-when-feature-enabled; yes; http://unsafe.url; blocked;'),
                    ('blocked/3.html.headers',
                     'Enable-Navigation-Blocking: allowed-url http://safe.url https://safe.url')]

        self.assert_generated(expected, generated=g.writer.fs)

    def assert_generated(self, expected, generated):
        self.assertEquals(len(expected), len(generated))
        expected = sorted(expected)
        i = 0
        for file_path, generated_value in sorted(generated.iteritems()):
            self.assertEquals(expected[i], (file_path, generated_value))
            i+=1


if __name__ == '__main__':
    unittest.main()
