# pylint: disable=missing-docstring

from pyff.pyff import pyff_module

TRIVIAL_MODULE = """import sys

def func():
    pass"""

IMPORT_MODULE = """import sys
from os import path

def func():
    pass"""

CLASSES_MODULE = """import sys

class Klass:
    pass

def func():
    pass"""


def test_trivial_module():
    difference = pyff_module(TRIVIAL_MODULE, TRIVIAL_MODULE)
    assert difference is None

def test_changed_module():
    difference = pyff_module(TRIVIAL_MODULE, IMPORT_MODULE)
    assert difference is not None
    assert len(difference) == 1

def test_module_with_new_class():
    difference = pyff_module(TRIVIAL_MODULE, CLASSES_MODULE)
    assert difference is not None
    assert len(difference) == 1
