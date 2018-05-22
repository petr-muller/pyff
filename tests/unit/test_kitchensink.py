# pylint: disable=missing-docstring

from pytest import raises
from colorama import Fore, Style
from pyff.kitchensink import HL_OPEN, HL_CLOSE, highlight


def test_highlights():
    output = f"1 {HL_OPEN}2{HL_CLOSE} 3 {HL_OPEN}4{HL_CLOSE}"
    colorized = f"1 {Fore.RED}2{Style.RESET_ALL} 3 {Fore.RED}4{Style.RESET_ALL}"
    quoted = "1 '2' 3 '4'"
    assert highlight(output, "color") == colorized
    assert highlight(output, "quotes") == quoted

    with raises(ValueError):
        highlight(output, "whatever")
