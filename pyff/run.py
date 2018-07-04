"""Entry point for the `pyff` command"""

import sys
import logging
import pathlib
from argparse import ArgumentParser
from typing import Callable

from pyff.modules import pyff_module_code
from pyff.packages import pyff_package
from pyff.kitchensink import highlight, HIGHLIGHTS

LOGGER = logging.getLogger(__name__)


def _pyff_that(function: Callable, what: str) -> None:
    parser = ArgumentParser()
    parser.add_argument("old")
    parser.add_argument("new")

    parser.add_argument("--highlight-names", dest="highlight", choices=HIGHLIGHTS, default="color")
    parser.add_argument("--debug", action="store_true", default=False)

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(
            format="%(levelname)s:%(name)s:%(funcName)s: %(message)s", level=logging.DEBUG
        )

    LOGGER.debug(f"Python Diff: old {what} {args.old} | new {what} {args.new}")
    changes = function(pathlib.Path(args.old), pathlib.Path(args.new))

    if changes is None:
        print(f"Pyff did not detect any significant difference between {args.old} and {args.new}")
        sys.exit(0)

    print(highlight(str(changes), args.highlight))


def pyffmod() -> None:
    """Entry point for the `pyff` command"""

    def compare(old, new):
        """Open two arguments as files and compare them"""
        with open(old, "r") as old_module, open(new, "r") as new_module:
            old_version = old_module.read()
            new_version = new_module.read()

        return pyff_module_code(old_version, new_version)

    _pyff_that(compare, "module")


def pyffpkg() -> None:
    """Entry point for the `pyff-package` command"""
    _pyff_that(pyff_package, "package")


if __name__ == "__main__":
    pyffmod()
