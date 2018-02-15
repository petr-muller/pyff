# pylint: disable=missing-docstring

from pytest import raises
from pyff.pyff import pyff_function

TRIVIAL_FUNCTION = """def func(): pass"""
TRIVIAL_FUNCTION_2 = """def func2(): pass"""

IMPLEMENTED_FUNCTION = """def func(): return None"""
FUNCTION_W_EXTERNAL_NAME = """def func(): parser = ArgumentParser()"""

def test_trivial_function():
    difference = pyff_function(TRIVIAL_FUNCTION, TRIVIAL_FUNCTION)
    assert difference is None

def test_name_change():
    difference = pyff_function(TRIVIAL_FUNCTION, TRIVIAL_FUNCTION_2)
    assert len(difference) == 1
    assert difference.name == "func"
    assert difference.names is not None
    assert difference.names.old == "func"
    assert difference.names.new == "func2"

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
    assert str(difference) == "Function 'func' changed implementation"

def test_changed_implementation_external_name(): # pylint: disable=invalid-name
    difference = pyff_function(TRIVIAL_FUNCTION, FUNCTION_W_EXTERNAL_NAME, old_imports=[],
                               new_imports=["ArgumentParser"])
    assert len(difference) == 1
    assert difference.names is None
    assert difference.implementation is not None
    assert (str(difference) ==
            "Function 'func' changed implementation, newly uses external names 'ArgumentParser'")
