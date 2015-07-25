import test_includes
import unittest
import generator

class MockWriter(object):
    fs = {}

    def write(self, filename, content):
        self.fs[filename] = content

class GeneratorTestCase(unittest.TestCase):

    def test_simple_generatesSelection(self):
        spec = {
            "specification": [
                {
                    "name": "citrus",
                    "description": "the family Rutaceae.",
                    "test_expansion": [
                        {
                            "name": "orange",
                            "color": "*",
                            "expectation": "sour"
                        },
                        {
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
                            "name": "pear",
                            "color": "*",
                            "expectation": "sweet"
                        },
                        {
                            "name": "apple",
                            "color": ["red", "green"],
                            "expectation": "sweet"
                        },
                    ]
                },
            ],
            "excluded_tests": [
                {
                    "name": "lemon",
                    "color": ["green", "red"],
                    "expectation": "*"
                },
                {
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
                        "matches": {
                            "name": "non_empty_string",
                            "color": "@color_schema",
                            "expectation": "@expectation_schema"
                        },
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
                    "matches": {
                        "name": "non_empty_string",
                        "color": "@color_schema",
                        "expectation": "@expectation_schema"
                    }
                }
            },
            "#color_schema": ["red", "green", "yellow"],
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

        expected = sorted(expected)
        self.assertEquals(len(expected), len(g.writer.fs))
        i = 0
        for file_path, generated_value in sorted(g.writer.fs.iteritems()):
            self.assertEquals(expected[i], (file_path, generated_value))
            i+=1

if __name__ == '__main__':
    unittest.main()
