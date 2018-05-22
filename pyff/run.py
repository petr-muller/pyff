"""Entry point for the `pyff` command"""

import sys  # pragma: no cover
from argparse import ArgumentParser  # pragma: no cover

from pyff.modules import pyff_module_code  # pragma: no cover
from pyff.kitchensink import highlight, HIGHLIGHTS  # pragma: no cover


def main() -> None:  # pragma: no cover
    """Entry point for the `pyff` command"""
    parser = ArgumentParser()
    parser.add_argument("old")
    parser.add_argument("new")

    parser.add_argument("--highlight-names", dest="highlight", choices=HIGHLIGHTS, default="color")

    args = parser.parse_args()

    with open(args.old, "r") as old, open(args.new, "r") as new:
        old_version = old.read()
        new_version = new.read()

    changes = pyff_module_code(old_version, new_version)

    if changes is None:
        print(f"Pyff did not detect any significant difference between {args.old} and {args.new}")
        sys.exit(0)

    print(highlight(str(changes), args.highlight))


if __name__ == "__main__":  # pragma: no cover
    main()
