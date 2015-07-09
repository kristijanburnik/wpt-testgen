import re, json

def get_template(basename):
    with open(os.path.join(template_directory, basename)) as f:
        return f.read()


def write_file(filename, contents):
    with open(filename, "w") as f:
        f.write(contents)


def read_nth_line(fp, line_number):
  fp.seek(0)
  for i, line in enumerate(fp):
    if (i + 1) == line_number:
      return line


def load_json(path_to_file):
    re_error_location = re.compile('line ([0-9]+) column ([0-9]+)')
    with open(path_to_file) as f:
        try:
            return json.load(f)
        except ValueError, ex:
            print "In:", path_to_file
            print ex.message
            match = re_error_location.search(ex.message)
            if match:
                line_number, column = int(match.group(1)), int(match.group(2))
                print read_nth_line(f, line_number).rstrip()
                print " " * (column - 1) + "^"
            sys.exit(1)
