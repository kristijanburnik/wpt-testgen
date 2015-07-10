import test_includes
import unittest
import generator

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
                            "color": ["green"]
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
            ]
        }

        schema = {
            "/": {
                "matches": {"specification": "non_empty_list"},
                "/specification/*": {
                    "matches": {
                        "name": "non_empty_string",
                        "description": "non_empty_string",
                        "test_expansion": "non_empty_list"
                    },
                    "/test_expansion/*": {
                        "path": "%(_name)s/%(color)s.html",
                        "template": "%(color)s %(name)s belongs to %(_description)s",
                        "matches": {
                            "name": "non_empty_string",
                            "color": "@color_schema"
                        }
                        # TODO: add a token saying this should be generated.
                    }
                }
            },
            "#color_schema": ["red", "green", "yellow"]
        }
        g = generator.Generator(spec, schema)
        results = g.generate()

        expected = [
            "citrus/red.html red orange belongs to the family Rutaceae.",
            "citrus/green.html green orange belongs to the family Rutaceae.",
            "citrus/yellow.html yellow orange belongs to the family Rutaceae.",
            "citrus/green.html green lemon belongs to the family Rutaceae.",
            "roses/red.html red pear belongs to the rose-type tree fruits.",
            "roses/green.html green pear belongs to the rose-type tree fruits.",
            "roses/yellow.html yellow pear belongs to the rose-type tree fruits.",
            "roses/red.html red apple belongs to the rose-type tree fruits.",
            "roses/green.html green apple belongs to the rose-type tree fruits."
        ]

        i = 0
        for file_path, generated_value in results:
            self.assertEquals(expected[i], file_path + " " + generated_value)
            i+=1

if __name__ == '__main__':
    unittest.main()
