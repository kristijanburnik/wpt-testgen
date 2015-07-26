from validator import Validator, SchemaError, SpecError, TemplateError
from util import load_json, normalize_path, filter_comments
import os
import re

class OutputWriter(object):
    def write(self, filename, content):
        full_path = os.path.dirname(filename)
        try:
            os.makedirs(full_path)
        except:
            pass
        with open(filename, "w") as f:
            f.write(content)

class DryRunWritter(object):
    def write(self, filename, content):
        print filename, content

class FileReader(object):
    def read(self, filename, paths=None):
        if paths is None:
            paths = [os.getcwd()]
        for path in paths:
            full_path = os.path.join(path, filename)
            if os.path.isfile(full_path):
                return open(full_path, "r").read()
        raise IOError("Cannot find file %s", filename)

class Generator(object):
    def __init__(self, spec, schema,
                 reader=None, writer=None, mode="release", paths=None):
        self.spec = spec
        self.schema = schema
        self.mode = mode
        self.writer = writer if not writer is None else OutputWriter()
        self.reader = reader if not reader is None else FileReader()
        self.paths = paths

    def generate(self, error_details={}):
        v = Validator(self.spec, self.schema)
        v.validate(error_details=error_details)
        self._leafs = v.leafs
        self._meta_schema_map = v.meta_schema_map
        self._re_integer_pattern = re.compile('^[0-9]+$')
        self._path_action = {}
        self._identify_path_actions(None, self.schema)
        self._excluded_selections = {}

        for expansion_node in self._traverse(None, self.spec,
                                             match_action="suppress"):
            path, named_chain, pattern = expansion_node
            for selection in self._permute_pattern(pattern):
                serialized_selection = self._serialize(selection)
                print "To be excluded", serialized_selection
                self._excluded_selections[serialized_selection] = True

        selection_index = -1
        for expansion_node in self._traverse(None, self.spec,
                                             match_action="generate"):
            path, named_chain, pattern = expansion_node
            for selection in self._permute_pattern(pattern):
                selection_index += 1
                serialized_selection = self._serialize(selection)
                if serialized_selection in self._excluded_selections:
                    print "Excluding", selection
                    continue
                print "Generating", selection
                extensions = self._leafs[path]["extensions"]
                extended_selection = self._extend(selection,
                                                  named_chain,
                                                  selection_index,
                                                  extensions)

                # When clause handler.
                when_rules = self._leafs[path]["when"]
                if not when_rules is None:
                    for when_rule in when_rules:
                        match_any_clause = when_rule["match_any"]
                        if not self._when_rule_match_any(match_any_clause,
                                                         extended_selection):
                            continue

                        for do_rule in when_rule["do"]:
                            action = do_rule["action"]

                            if action == "generate":
                                # TODO(kristijanburnik): This is duplicated from below.
                                path_template = do_rule["path"]
                                content_template = self._resolve_template(
                                        do_rule["template"], extended_selection)
                                file_path = self._produce(path_template, extended_selection)
                                content = self._produce(content_template,
                                                        extended_selection,
                                                        reference=do_rule["template"])
                                self.writer.write(file_path, content)
                            elif action == "set_extension":
                                content_template = self._resolve_template(
                                        do_rule["template"], extended_selection)
                                content = self._produce(content_template,
                                                        extended_selection,
                                                        reference=do_rule["template"])
                                extended_selection[do_rule["key"]] = content
                            else:
                                raise ValueError("Invalid do action: %s" % action)

                # The generate action.
                path_template = self._leafs[path]["path"]
                content_template = self._resolve_template(
                    self._leafs[path]["template"], extended_selection)
                file_path = self._produce(path_template,
                                          extended_selection,
                                          check_produces=False)
                content = self._produce(content_template,
                                        extended_selection,
                                        reference=self._leafs[path]["template"],
                                        check_produces=False)
                self.writer.write(file_path, content)


    def _produce(self, template, values, reference="inline",
                 check_produces=False):
        try:
            produced_value = template % values
            if check_produces and produced_value == template:
                raise TemplateError("Template did not produce a value:\n%s" % \
                                    str(reference))
            return produced_value
        except ValueError, err:
            # TODO(kristijanburnik): Parse the index and show the caret pointer.
            # TODO(kristijanburnik): Add a test for this.
            raise SchemaError("Invalid template:\n%s\n\nValueError: %s" % \
                              (template, err.message))
        except KeyError, err:
            # TODO(kristijanburnik): Parse the index and show the caret pointer.
            # TODO(kristijanburnik): Add a test for this.
            raise SchemaError("Invalid template:\n%s\n\nKeyError: %s" % \
                              (template, err.message))


    def _serialize(self, selection):
        # TODO(kristijanburnik): this is a hack to omit names. It should be
        # documented or there should be a way to specify which patterns match.
        return str(filter_comments(selection))

    def _when_rule_match_any(self, match_any_clause, extended_selection):
        for first, second in match_any_clause:
            first %= extended_selection
            second %= extended_selection
            if first == second:
                return True
        return False

    def _resolve_template(self, mixed, extended_selection):
        if isinstance(mixed, dict):
            # TODO(kristijanburnik): Raise error if missing key for template.
            filename = mixed["__main__"] % extended_selection
            template = self.reader.read(filename, self.paths)

            # Unwrap and apply the subtemplates first.
            # TODO(kristijanburnik): This is hacky and not very useful in
            # general. A template generating order and dependency should be part
            # of the language of testgen.
            if len(mixed) == 1:
                return template

            for template_key, filename_pattern in mixed.iteritems():
                subtemplate_filename = self._produce(filename_pattern,
                                                     extended_selection,
                                                     reference=(filename, template_key),
                                                     check_produces=False)
                subtemplate = self.reader.read(subtemplate_filename, self.paths)
                extended_selection[template_key] = self._produce(
                    subtemplate, extended_selection, reference=template_key,
                    check_produces=False)

            return template
        else:
            return mixed

    def _extend(self, selection, named_chain, selection_index,
                extensions=None):
        """Populates selection with reference to parent nodes in spec.
           Values are prefixed with _ for each level. Default extensions can
           also be specified by the schema"""

        expanded = {}
        if not extensions is None:
            expanded.update(extensions)

        expanded.update({
            "__mode__": self.mode,
            "__index__": selection_index
        })

        expanded.update(selection)

        prefix = "_"
        for ancestor in reversed(named_chain):
            for k, v in ancestor.iteritems():
                expanded[prefix + k] = v
            prefix += "_"
        return expanded

    def _permute_pattern(self, pattern):
        for selection in self._permute(pattern, pattern.keys()):
            yield selection

    def _permute(self, pattern, key_order=[], key_index=0, selection=None):
        if selection is None:
            selection = {}

        if key_index >= len(key_order):
            yield selection
            return

        key = key_order[key_index]
        for value in pattern[key]:
            selection[key] = value
            for next_selection in self._permute(pattern,
                                                key_order,
                                                key_index + 1,
                                                selection):
                yield next_selection

    def _as_assoc(self, mixed):
        if isinstance(mixed, dict):
            for key, value in mixed.iteritems():
                yield (key, value)
        elif isinstance(mixed, list):
            key = 0
            for value in mixed:
                yield (key, value)
                key += 1

    def _is_assoc(self, mixed):
        return isinstance(mixed, dict) or isinstance(mixed, list)

    def _is_leaf(self, path):
        return path in self._leafs

    def _generalize_path(self, path):
        parts = path.split('/')
        for i in range(0, len(parts)):
            if self._re_integer_pattern.match(parts[i]):
                parts[i] = "*"
        return '/' + '/'.join(filter(None, parts))

    def _expand_pattern(self, pattern, generic_path):
        for k, v in pattern.iteritems():
            item_path = generic_path + "/" + k
            if item_path in self._meta_schema_map and v == "*":
                pattern[k] = self._meta_schema_map[item_path]
            elif not self._is_assoc(v):
                pattern[k] = [v]

        return pattern

    def _identify_path_actions(self, key, value, path="/"):
        generic_path = self._generalize_path(path)

        if "action" in value:
            generic_path = self._generalize_path(path)
            self._path_action[generic_path] = value["action"]
            return

        if not self._is_assoc(value):
            return

        for k, v in self._as_assoc(value):
            self._identify_path_actions(k, v, path + "/" + str(k))

    def _traverse(self, key, value, path="/", named_chain=[],
                  match_action=None):
        generic_path = self._generalize_path(path)
        if self._is_leaf(generic_path):
            if self._path_action.get(generic_path, None) != match_action:
                return
            expanded_pattern = self._expand_pattern(value, generic_path)
            yield generic_path, named_chain, expanded_pattern
            return

        for k, v in self._as_assoc(value):
            if not self._is_assoc(v):
                continue

            next_path = normalize_path(path + "/" + str(k))
            next_generic_path = self._generalize_path(next_path)

            if "name" in v and not self._is_leaf(next_generic_path):
                next_name = [v]
            else:
                next_name = []

            for expansion_node in self._traverse(k, v, path=next_path,
                                                 named_chain=named_chain + \
                                                             next_name,
                                                 match_action=match_action):
                yield expansion_node

def run_generator(args):
    import json, sys
    # Grab the spec's and schema's path.
    search_paths = {}
    for filename in [args.spec, args.schema]:
        path = os.path.abspath(os.path.dirname(os.path.expanduser(filename)))
        search_paths[path] = True

    spec = load_json(args.spec)
    schema = load_json(args.schema)
    writer = OutputWriter() if not args.dryrun else DryRunWritter()
    reader = FileReader()
    generator = Generator(spec, schema,
                          writer=writer,
                          reader=reader,
                          mode=args.target,
                          paths=search_paths.keys())
    error_details = {}
    try:
        generator.generate(error_details=error_details)
        return
    except SchemaError, err:
        print 'Schema Error:', err.message
    except SpecError, err:
        print 'Spec Error:', err.message
        print json.dumps(error_details, indent=2)

    sys.exit(1)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='TestGen generator utility')
    # TODO(kristijanburnik): Merge as common options.
    parser.add_argument('-s', '--spec', type=str, required=True,
        help='Specification file used for describing test scenarios')
    parser.add_argument('-v', '--schema', type=str, required=True,
        help='Schema file for validating and generating from specification')
    # TODO(kristijanburnik): Add an option for a single file incorporating
    # the spec and validation schema, all in one.
    parser.add_argument("--dryrun", action='store_true', default=False,
                        help="Display what is to be generated.")
    parser.add_argument('-t', '--target', type = str,
        choices = ("release", "debug"), default = "release",
        help = 'Sets the appropriate mode for generating tests')
    args = parser.parse_args()
    run_generator(args)


if __name__ == "__main__":
    main()
