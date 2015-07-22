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

### Example test suite

Let Browser X implement a security feature which tells if a navigation to a link
should be blocked or not.

The feature can be enabled by providing an HTTP header

```HTTP
Enable-Navigation-Blocking: allowed-url http://some.url
```

We could start testing with something very basic.

Let's test if the browser is allowing all navigations if the feature is
disabled. We can write the whole scenario by a single expansion pattern:

```json
// ...
{
  "name": "allowed-when-feature-not-enabled",
  "description": "All navigations allowed if feature is disabled.",
  "feature_enabled": "no"
  "url": "*",
  "expectation": "allowed"
}
// ...

```

We can specify by the schema what the valid values are,
and define which values we can use and expand into:

```json
// ...
{
  "/*": {
    "matches": {
      "name": "non_empty_string",
      "description": "non_empty_string"
      "feature_enabled": ["no", "yes"],
      "url": "@url_schema",
      "expectation": ["allowed", "blocked"]
    },
    // ...
  }
  "#url_schema": ["http://safe.url", "https://safe.url", "http://unsafe.url"]
}
// ...
```

Notice we can define our custom subschemas by the "#" prefix and then reference
them by "@".

--

By running the ```generator.py``` we expand our pattern to 3 concrete
scenarios:

```json
{
  "index": 0,
  "name": "allowed-when-feature-not-enabled",
  "description": "All navigations allowed if feature is disabled.",
  "feature_enabled": "no"
  "url": "http://safe.url",
  "expectation": "allowed"
},
{
  "index": 1,
  "name": "allowed-when-feature-not-enabled",
  "description": "All navigations allowed if feature is disabled.",
  "feature_enabled": "no"
  "url": "https://safe.url",
  "expectation": "allowed"
},
{
  "index": 2,
  "name": "allowed-when-feature-not-enabled",
  "description": "All navigations allowed if feature is disabled.",
  "feature_enabled": "no"
  "url": "http://unsafe.url",
  "expectation": "allowed"
}

```

Each of these three scenarios gets it's own HTML file, however we have to
specify a bit more in the schema to instruct the generator how to do it:

```json
// ...
{
  "/*": {
      "matches": {
        "name": "non_empty_string",
        "description": "non_empty_string"
        "feature_enabled": ["no", "yes"],
        "url": "@url_schema",
        "expectation": ["allowed", "blocked"]
      },
      "action": "generate",
      "path": "safe-links/%(expectation)s/%(index)s.html"
      // ...
    }
    "#url_schema": ["http://safe.url", "https://safe.url", "http://unsafe.url"]
}
// ...
```

The "/*" key matches each value in the root node "/" of the specification json.
The "*" part of the key is a for-each substitution (e.g. for each value in an
array).

The keyword ```matches``` is used to specify valid values

The keyword ```action``` specifies what is to be done with this node in th JSON.
Here we want to **generate** a file for all nodes at level "/*". Other possible
value would be **suppress** which would skip a scenario when matched.

You've guessed it! The ```path``` is used to define a substitution template
for the path in which we place the test. In this case we will end up having:

* safe-links/allowed/0.html
* safe-links/allowed/1.html
* safe-links/allowed/2.html

--

Now, we need a template file for our test, let's do something very simple:

```

<html>
<head>
  <title>%(name)s</title>
  <meta name="description" content="%(description)s">
  <script src="/resources/testharness.js"></script>
  <script src="/resources/testharnessreport.js"></script>
  <script src="/safe-links/generic/safe-links-test-case.js"></script>
</head>
<body>
</body>
</html>
