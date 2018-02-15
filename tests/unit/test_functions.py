# pylint: disable=missing-docstring

from pytest import raises
from pyff.pyff import pyff_function

TRIVIAL_FUNCTION = """def function(): pass"""
TRIVIAL_FUNCTION_2 = """def function2(): pass"""

IMPLEMENTED_FUNCTION = """def function(): return None"""

def test_trivial_function():
    difference = pyff_function(TRIVIAL_FUNCTION, TRIVIAL_FUNCTION)
    assert difference is None

def test_name_change():
    difference = pyff_function(TRIVIAL_FUNCTION, TRIVIAL_FUNCTION_2)
    assert len(difference) == 1
    assert difference.name == "function"
    assert difference.names is not None
    assert difference.names.old == "function"
    assert difference.names.new == "function2"

def test_not_functions():
    no_func = "a = 1"
    two_func = """def f(): pass
def g(): pass"""

    for bad in (no_func, two_func):
        with raises(ValueError):
            pyff_function(TRIVIAL_FUNCTION, bad)
        with raises(ValueError):
            pyff_function(bad, TRIVIAL_FUNCTION)

def test_changed_implementation():
    difference = pyff_function(TRIVIAL_FUNCTION, IMPLEMENTED_FUNCTION)
    assert len(difference) == 1
    assert difference.names is None
    assert difference.implementation is not None
    assert str(difference) == "Function 'function' changed implementation"
