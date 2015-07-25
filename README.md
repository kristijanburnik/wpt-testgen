# WPT TestGen

## Framework for specifying and generating Web Platform Tests

WPT TestGen is a set of tools for specifying test scenarios by using a higher
level language.

The principle for this approach to writing tests is that one should be able to
briefly describe the scenarios and expectations for tests without having to deal
with too much boilerplate and keep the test suite easier to maintain.

An author can start of by writing two files, a **Specification** and  a
**Schema**.

The Specification describes what is being tested: the scenario
and the expected outcome.

The Schema is used for:

* Making sure the specification is valid, e.g.: no typos or invalid enumerated
values are being used and that each specification section is coherent and easy
to understand
* To enumerate valid values for each entry in the specification
* Determining how tests are being generated: by supplying templates for desired
paths and test files
* Determining which part of the specification is used for suppressing/skipping
tests and scenarios.

The test logic should reside in the HTML and JS template files and in a one
or more JS files which exercise the tests.

## Expansion Patterns

The most powerful feature of WPT TestGen is the ability to specify patterns in
a very short notation.

Each field in an expansion pattern can be in one of the following formats:

* Single match: ```"value"```

* Match any of: ```["value1", "value2", ...]```

* Match all: ```"*"```


So let's view this in action by testing our new awesome browser security
feature!

## Example test suite

Let Browser X implement a security feature which allows a web developer to
specify if a navigation to a URL should be blocked or not.

The feature can be enabled by providing an HTTP header

```HTTP
Enable-Navigation-Blocking: allowed-url http://some.url
```

We could start testing with something very basic.

Let's test if the browser is allowing all navigations if the feature is
disabled. We can write the whole scenario by a single expansion pattern:

```json
{
  "tests": [
    {
      "name": "allowed-when-feature-not-enabled",
      "description": "All navigations allowed if feature is disabled.",
      "feature_enabled": "no",
      "url": "*",
      "expectation": "allowed"
    }
  ]
}

```

We can specify by the schema what the valid values are,
and define which values we can use and expand into:

```json
// ...
{
  "/tests/*": {
    "matches": {
      "name": "non_empty_string",
      "description": "non_empty_string",
      "feature_enabled": ["no", "yes"],
      "url": "@url_schema",
      "expectation": ["allowed", "blocked"]
    }
    // ...
  },
  "#url_schema": ["http://safe.url", "https://safe.url", "http://unsafe.url"]
}
// ...
```

Notice we can define our custom subschemas by the "#" prefix and then reference
them by "@".


## Generating the Tests

By running the ```generator.py```, behind the scenes we expand our pattern to 3
concrete scenarios (notice the different URL):

```json
{
  "__index__": 0,
  "name": "allowed-when-feature-not-enabled",
  "description": "All navigations allowed if feature is disabled.",
  "feature_enabled": "no",
  "url": "http://safe.url",
  "expectation": "allowed"
},
{
  "__index__": 1,
  "name": "allowed-when-feature-not-enabled",
  "description": "All navigations allowed if feature is disabled.",
  "feature_enabled": "no",
  "url": "https://safe.url",
  "expectation": "allowed"
},
{
  "__index__": 2,
  "name": "allowed-when-feature-not-enabled",
  "description": "All navigations allowed if feature is disabled.",
  "feature_enabled": "no",
  "url": "http://unsafe.url",
  "expectation": "allowed"
}

```

Each of these three scenarios gets it's own HTML file, however we have to
specify a bit more in the schema to instruct the generator how to do it:

```json
// ...
{
  "/tests/*": {
      "matches": {
        "name": "non_empty_string",
        "description": "non_empty_string",
        "feature_enabled": ["no", "yes"],
        "url": "@url_schema",
        "expectation": ["allowed", "blocked"]
      },
      "action": "generate",
      "path": "safe-links/%(expectation)s/%(__index__)s.html"
      // ...
    },
    "#url_schema": ["http://safe.url", "https://safe.url", "http://unsafe.url"]
}
// ...
```

The "/tests/\*" key matches each value in the path starting from the root node
"/" of the specification json.
The "\*" part of the key is a for-each substitution (i.e. for each value in the
"tests" array).

The keyword ```matches``` is used to specify valid values which can live in the
JSON node.

The keyword ```action``` specifies what is to be done with this node in the
JSON. Here we want to `generate` a file for all nodes at level "/\*". Other
possible value would be `suppress` indicating to skip a scenario when matched.

You've guessed it! The ```path``` is used to define a substitution template
for the path in which we place the test. In this case we will end up having:

* safe-links/allowed/0.html
* safe-links/allowed/1.html
* safe-links/allowed/2.html


## Templates

Now, we need a template file for our tests, let's do something very simple:

```html
<html>
<head>
  <title>%(name)s</title>
  <meta name="description" content="%(description)s">
  <script src="/resources/testharness.js"></script>
  <script src="/resources/testharnessreport.js"></script>
  <script src="/safe-links/generic/safe-links-test-case.js"></script>
</head>
<body>
  <script>
    var scenario = {
      "name": "%(name)",
      "description": "%(description)s",
      "feature_enabled": "%(feature_enabled)s",
      "url": "%(url)s",
      "expectation": "%(expectation)s"
    };
    SafeLinksTestCase(scenario).start();
 </script>
</body>
</html>
```

After generating, we end up with 3 files as mentioned above, e.g. the first one:

* safe-links/allowed/0.html

```html
<html>
<head>
  <title>allowed-when-feature-not-enabled</title>
  <meta name="description" content="All navigations allowed if feature is disabled.">
  <script src="/resources/testharness.js"></script>
  <script src="/resources/testharnessreport.js"></script>
  <script src="/safe-links/generic/safe-links-test-case.js"></script>
</head>
<body>
  <script>
    var scenario = {
      "name": "allowed-when-feature-not-enabled",
      "description": "All navigations allowed if feature is disabled.",
      "feature_enabled": "no",
      "url": "http://safe.url",
      "expectation": "allowed"
    };
    SafeLinksTestCase(scenario).start();
 </script>
</body>
</html>
```

The other two files (safe-links/allowed/1.html and safe-links/allowed/2.html)
would only differ by the URL portion of the scenario.

Let's save our template into `safe-links/generic/template/test.html.template`
We can then reference it by the schema:

```json
{
  "/*": {
      "matches": {
        "name": "non_empty_string",
        "description": "non_empty_string",
        "feature_enabled": ["no", "yes"],
        "url": "@url_schema",
        "expectation": ["allowed", "blocked"]
      },
      "action": "generate",
      "path": "safe-links/%(expectation)s/%(__index__)s.html",

      "template": {
        "__main__": "safe-links/generic/template/test.html.template"
      }

    },
    "#url_schema": ["http://safe.url", "https://safe.url", "http://unsafe.url"]
}
```


## Even more templates

Since our tests rely on setting HTTP headers and WPT supports `*.headers` files,
we should specify what additional files are getting generated along with the
HTML:

```json
{
  "/*": {
      "matches": {
        "name": "non_empty_string",
        "description": "non_empty_string",
        "feature_enabled": ["no", "yes"],
        "url": "@url_schema",
        "expectation": ["allowed", "blocked"]
      },
      "action": "generate",
      "path": "safe-links/%(expectation)s/%(__index__)s.html",
      "template": {
        "__main__": "safe-links/generic/template/test.html.template"
      },

      "when": [{
        "match_any": [["%(feature_enabled)s", "yes"]],
        "action": "generate",
        "path": "safe-links/%(expectation)s/%(__index__)s.html.headers",
        "template": "Enable-Navigation-Blocking: allowed-url http://safe.url https://safe.url"
      }]

    },
    "#url_schema": ["http://safe.url", "https://safe.url", "http://unsafe.url"]
}
```

The ```when``` keyword is used to check for a match and perform the action for
the given concrete scenario.
Matching can be done in an OR fashion with "match_any", and AND fashion with
"match_all".

Also, notice that we can specify a template inline, without a need for an extra
template file.

## The Test Logic

Since the HTML files generated by TestGen are pretty generic, we need to do
more in a separate JS file. Here I write some imaginary code to display the
idea.


* safe-links/generic/safe-links-test-case.js

```javascript

function SafeLinksTestCase(scenario) {
  this.scenario = scenario;
}

SafeLinksTestCase.prototype.start = function() {
  test(function() {

    var a = document.createElement("a");
    a.href = this.scenario.url;
    document.body.appendChild(a):

    a.addEventListener("imaginary-success-event", function() {
      assert_equals(this.scenario.expectation, "allowed",
                    "The request to the URL should be allowed.");
    });

    a.addEventListener("imaginary-error-event", function() {
      assert_equals(this.scenario.expectation, "blocked",
                    "The request to the URL should be blocked.");
    })

    a.click();

  }, this.scenario.description);
}


```

## A bit more expansion

TODO(kristijanburnik): TBD

## Wrapping things up

TODO(kristijanburnik): TBD
