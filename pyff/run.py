"""Entry point for the `pyff` command"""

import sys # pragma: no cover
from argparse import ArgumentParser # pragma: no cover
from colorama import Fore, Style

from pyff.pyff import pyff_module # pragma: no cover
from pyff.kitchensink import HL_OPEN, HL_CLOSE

HIGHLIGHTS = ("color", "quotes")

def highlight(message: str, highlights: str) -> str:
    """Replace highlight placeholders in a given string using selected method"""
    if highlights == "color":
        return (message.replace(HL_OPEN, Fore.RED)
                .replace(HL_CLOSE, Style.RESET_ALL))
    elif highlights == "quotes":
        return message.replace(HL_OPEN, "'").replace(HL_CLOSE, "'")

    raise ValueError("Highlight should be one of: " + str(HIGHLIGHTS))

def main() -> None: # pragma: no cover
    """Entry point for the `pyff` command"""
    parser = ArgumentParser()
    parser.add_argument("old")
    parser.add_argument("new")

    parser.add_argument("--highlight-names", dest="highlight", choices=HIGHLIGHTS,
                        default="color")

    args = parser.parse_args()

    with open(args.old, 'r') as old, open(args.new, 'r') as new:
        old_version = old.read()
        new_version = new.read()

    changes = pyff_module(old_version, new_version)

    if changes is None:
        print(f"Pyff did not detect any significant difference between {args.old} and {args.new}")
        sys.exit(0)

    print(highlight(str(changes), args.highlight))


if __name__ == "__main__": # pragma: no cover
    main()
