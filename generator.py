from validator import Validator
import re

class Generator(object):
    def __init__(self, spec, schema):
        self.spec = spec
        self.schema = schema

    def generate(self):
        v = Validator(self.spec, self.schema)
        v.validate()
        self._leafs = v.leafs
        self._meta_schema_map = v.meta_schema_map
        self._re_integer_pattern = re.compile('^[0-9]+$')
        for expansion_node in self._traverse(None, self.spec):
            path, named_chain, pattern = expansion_node
            for selection in self._permute_pattern(pattern):
                extended_selection = self._extend(selection, named_chain)
                file_path = self._leafs[path][0] % extended_selection
                generated_value =  self._leafs[path][1] % extended_selection
                yield file_path, generated_value

    def _extend(self, selection, named_chain):
        """Populates selection with reference to parent nodes in spec.
           Values are prefixed with _ for each level"""
        expanded = {}
        for k, v in selection.iteritems():
            expanded[k] = v

        prefix = "_"
        for ancestor in reversed(named_chain):
            for k, v in ancestor.iteritems():
                expanded[prefix + k] = v
            prefix += "_"
        return expanded

    def _permute_pattern(self, pattern):
        for selection in self._permute(pattern, pattern.keys()):
            yield selection

    def _permute(self, pattern, key_order=[], key_index=0, selection={}):
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
        return '/'.join(parts)

    def _expand_pattern(self, pattern, generic_path):
        for k, v in pattern.iteritems():
            item_path = generic_path + "/" + k
            if item_path in self._meta_schema_map and v == "*":
                pattern[k] = self._meta_schema_map[item_path]
            elif not self._is_assoc(v):
                pattern[k] = [v]

        return pattern


    def _traverse(self, key, value, path="/", named_chain=[]):
        generic_path = self._generalize_path(path)
        if self._is_leaf(generic_path):
            expanded_pattern = self._expand_pattern(value, generic_path)
            yield generic_path, named_chain, expanded_pattern
            return

        for k, v in self._as_assoc(value):
            if not self._is_assoc(v):
                continue

            next_path = path + "/" + str(k)
            next_generic_path = self._generalize_path(next_path)
            next_name = [v] if "name" in v and not self._is_leaf(next_generic_path) else []

            for expansion_node in self._traverse(k, v, path=next_path,
                                                  named_chain=named_chain + \
                                                              next_name):
                yield expansion_node



