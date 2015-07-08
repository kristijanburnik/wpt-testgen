
def assert_non_empty_string(obj, field):
    assert field in obj, 'Missing field "%s"' % field
    assert isinstance(obj[field], basestring), \
        'Field "%s" must be a string' % field
    assert len(obj[field]) > 0, 'Field "%s" must not be empty' % field


def assert_non_empty_list(obj, field):
    assert isinstance(obj[field], list), \
        '%s must be a list' % field
    assert len(obj[field]) > 0, \
        '%s list must not be empty' % field


def assert_non_empty_dict(obj, field):
    assert isinstance(obj[field], dict), \
        '%s must be a dict' % field
    assert len(obj[field]) > 0, \
        '%s dict must not be empty' % field


def assert_contains(obj, field):
    assert field in obj, 'Must contain field "%s"' % field


def assert_string_from(obj, field, items):
   assert obj[field] in items, \
        'Field "%s" must be from: %s' % (field, str(items))


def assert_string_or_list_items_from(obj, field, items):
    if isinstance(obj[field], basestring):
        assert_string_from(obj, field, items)
        return

    assert isinstance(obj[field], list), "%s must be a list!" % field
    for allowed_value in obj[field]:
        assert allowed_value != '*', "Wildcard is not supported for lists!"
        assert allowed_value in items, \
            'Field "%s" must be from: %s' % (field, str(items))


def assert_contains_only_fields(obj, expected_fields):
    for expected_field in expected_fields:
        assert_contains(obj, expected_field)

    for actual_field in obj:
        assert actual_field in expected_fields, \
                'Unexpected field "%s".' % actual_field


def assert_value_unique_in(value, used_values):
    assert value not in used_values, 'Duplicate value "%s"!' % str(value)
    used_values[value] = True


def assert_valid_artifact(exp_pattern, artifact_key, schema):
    if isinstance(schema, list):
        assert_string_or_list_items_from(exp_pattern, artifact_key,
                                         ["*"] + schema)
        return

    for sub_artifact_key, sub_schema in schema.iteritems():
        assert_valid_artifact(exp_pattern[artifact_key], sub_artifact_key,
                              sub_schema)
