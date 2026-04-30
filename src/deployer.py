import os
import re
import sys

import yaml


SNOWFLAKE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snowflake")
PROD_YAML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prod.yaml")


def tryint(s):
    try:
        return int(s)
    except ValueError:
        return s


def alphanum_key(s):
    """Turn a string into a list of string and number chunks for lexicographic sort.
    "z22a" -> ["z", 22, "a"]
    """
    return [tryint(c) for c in re.split(r"(\d+)", s)]


def collect_files_non_prod():
    """Walk src/snowflake and collect all .sql files in lexicographic order."""
    files = []
    for subdir, dirs, filenames in os.walk(SNOWFLAKE_DIR, topdown=True):
        dirs.sort(key=alphanum_key)
        for filename in sorted(filenames, key=alphanum_key):
            if filename.endswith(".sql"):
                files.append(os.path.join(subdir, filename))
    return sorted(files, key=alphanum_key)


def collect_files_prod():
    """Read prod.yaml and collect whitelisted files relative to src/snowflake."""
    with open(PROD_YAML) as f:
        paths = yaml.safe_load(f)

    if not paths:
        raise ValueError("prod.yaml is empty or invalid")

    files = []
    for path in paths:
        full_path = os.path.join(SNOWFLAKE_DIR, path)
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"File listed in prod.yaml not found: {full_path}")
        files.append(full_path)
    return files


def relative_path(file):
    return os.path.relpath(file, SNOWFLAKE_DIR)


def execute_files(files):
    for file in files:
        print(f"Executing {relative_path(file)}")


def main():
    env = os.environ.get("ENV")
    if env is None:
        print("ERROR: ENV environment variable is not set. Use NON_PROD or PROD.", file=sys.stderr)
        sys.exit(1)

    if env == "NON_PROD":
        print("Running in NON-PROD mode: executing all files lexicographically.")
        files = collect_files_non_prod()
    elif env == "PROD":
        print("Running in PROD mode: executing whitelisted files from prod.yaml.")
        files = collect_files_prod()
    else:
        print(f"ERROR: Unknown ENV value '{env}'. Use NON_PROD or PROD.", file=sys.stderr)
        sys.exit(1)

    print(f"Files to execute ({len(files)}):")
    for f in files:
        print(f"  {relative_path(f)}")
    print()

    execute_files(files)


if __name__ == "__main__":
    main()
