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
                            "color": "*"
                        },
                        {
                            "name": "lemon",
                            "color": "*"
                        },
                    ]
                },
                {
                    "name": "roses",
                    "description": "the rose-type tree fruits.",
                    "test_expansion": [
                        {
                            "name": "pear",
                            "color": "*"
                        },
                        {
                            "name": "apple",
                            "color": ["red", "green"]
                        },
                    ]
                },
            ],
            "excluded_tests": [
                {
                    "name": "lemon",
                    "color": ["green", "red"]
                },
                {
                    "name": "orange",
                    "color": "green"
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
                        "test_expansion": "non_empty_list"
                    },
                    "/test_expansion/*": {
                        "path": "%(_name)s/%(color)s-%(name)s.html",
                        "template": "%(color)s %(name)s is of %(_description)s",
                        "action": "generate",
                        "matches": {
                            "name": "non_empty_string",
                            "color": "@color_schema"
                        }
                    }
                },
                "/excluded_tests/*": {
                    "action": "suppress",
                    "matches": {
                        "name": "non_empty_string",
                        "color": "@color_schema"
                    }
                }
            },
            "#color_schema": ["red", "green", "yellow"]
        }

        g = generator.Generator(spec, schema, writer=MockWriter())

        g.generate()

        expected = [('roses/green-pear.html',
                     'green pear is of the rose-type tree fruits.'),
                    ('citrus/yellow-lemon.html',
                     'yellow lemon is of the family Rutaceae.'),
                    ('roses/green-apple.html',
                     'green apple is of the rose-type tree fruits.'),
                    ('citrus/yellow-orange.html',
                     'yellow orange is of the family Rutaceae.'),
                    ('citrus/red-orange.html',
                     'red orange is of the family Rutaceae.'),
                    ('roses/red-pear.html',
                     'red pear is of the rose-type tree fruits.'),
                    ('roses/red-apple.html',
                     'red apple is of the rose-type tree fruits.'),
                    ('roses/yellow-pear.html',
                     'yellow pear is of the rose-type tree fruits.')]
        i = 0
        for file_path, generated_value in g.writer.fs.iteritems():
            self.assertEquals(expected[i], (file_path, generated_value))
            i+=1

if __name__ == '__main__':
    unittest.main()
