import glob
import os
import re
import sys

import yaml


SNOWFLAKE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snowflake")
PROD_D_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prod.d")
NON_PROD_D_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "non_prod.d")
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


def _load_d_dir(d_dir, fallback_yaml=None):
    """Read all .yaml files from a .d/ directory (sorted by filename) and return
    a merged list of paths relative to src/snowflake.

    If the .d/ directory doesn't exist, falls back to a single legacy YAML file
    (if provided and it exists).
    """
    dir_list = []

    if os.path.isdir(d_dir):
        for yaml_file in sorted(glob.glob(os.path.join(d_dir, "*.yaml"))):
            with open(yaml_file) as f:
                team_list = yaml.safe_load(f)
                if team_list:
                    print(f"Loaded {os.path.relpath(yaml_file)}: {len(team_list)} entries")
                    dir_list.extend(team_list)
    elif fallback_yaml and os.path.isfile(fallback_yaml):
        with open(fallback_yaml) as f:
            dir_list = yaml.safe_load(f)
            print(f"Loaded {os.path.relpath(fallback_yaml)} (legacy): {len(dir_list)} entries")

    if not dir_list:
        raise ValueError(f"No deployment entries found in {d_dir} or {fallback_yaml}")

    files = []
    for path in dir_list:
        full_path = os.path.join(SNOWFLAKE_DIR, path)
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"File listed in deployment config not found: {full_path}")
        files.append(full_path)
    return files


def collect_files_non_prod():
    """Read non_prod.d/*.yaml (or fallback to walking all .sql files) and collect
    whitelisted files relative to src/snowflake."""
    if os.path.isdir(NON_PROD_D_DIR) or os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), "non_prod.yaml")):
        return _load_d_dir(NON_PROD_D_DIR, fallback_yaml=os.path.join(os.path.dirname(os.path.abspath(__file__)), "non_prod.yaml"))

    # Legacy behaviour: walk src/snowflake and collect all .sql files lexicographically
    files = []
    for subdir, dirs, filenames in os.walk(SNOWFLAKE_DIR, topdown=True):
        dirs.sort(key=alphanum_key)
        for filename in sorted(filenames, key=alphanum_key):
            if filename.endswith(".sql"):
                files.append(os.path.join(subdir, filename))
    return sorted(files, key=alphanum_key)


def collect_files_prod():
    """Read prod.d/*.yaml (or fallback to prod.yaml) and collect whitelisted files relative to src/snowflake."""
    return _load_d_dir(PROD_D_DIR, fallback_yaml=PROD_YAML)


# Reference implementation provided as a starting point for contributors.
def collect_files_changed():
    """Collect .sql files under src/snowflake that changed vs. origin/master."""
    import subprocess
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/master...HEAD"],
        capture_output=True, text=True, check=True
    )
    changed = result.stdout.splitlines()
    files = []
    for path in changed:
        full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), path)
        if full_path.startswith(SNOWFLAKE_DIR) and path.endswith(".sql"):
            if os.path.isfile(full_path):
                files.append(full_path)
    return sorted(files, key=alphanum_key)


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
        print("Running in NON-PROD mode: executing whitelisted files from non_prod.d/.")
        files = collect_files_non_prod()
    elif env == "PROD":
        print("Running in PROD mode: executing whitelisted files from prod.d/.")
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
