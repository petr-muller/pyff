"""Placeholders for various elements in output"""

from typing import Iterable, Union, Sized, cast
from colorama import Fore, Style

HL_OPEN = "``"
HL_CLOSE = "''"

HIGHLIGHTS = ("color", "quotes")


def highlight(message: str, highlights: str) -> str:
    """Replace highlight placeholders in a given string using selected method"""
    if highlights == "color":
        return message.replace(HL_OPEN, Fore.RED).replace(HL_CLOSE, Style.RESET_ALL)
    elif highlights == "quotes":
        return message.replace(HL_OPEN, "'").replace(HL_CLOSE, "'")

    raise ValueError("Highlight should be one of: " + str(HIGHLIGHTS))


def hl(what: str) -> str:  # pylint: disable=invalid-name
    """Return highlighted string"""
    return f"{HL_OPEN}{what}{HL_CLOSE}"


def pluralize(name: str, items: Union[Sized, int]) -> str:
    """Return a pluralized name unless there is exactly one element in container."""
    try:
        return f"{name}" if len(cast(Sized, items)) == 1 else f"{name}s"
    except TypeError:
        return f"{name}" if cast(int, items) == 1 else f"{name}s"


def hlistify(container: Iterable) -> str:
    """Returns a comma separated list of highlighted names."""
    return ", ".join([hl(name) for name in container])
