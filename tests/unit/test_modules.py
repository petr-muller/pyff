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
    def method(self):
        pass
    def _method(self):
        pass
def func():
    pass"""

CHANGED_FUNCTION_MODULE = """import sys
def func():
    return None"""

IMPORT_USAGE_MODULE = """import sys
from os import path
def func():
    return path()"""

def test_trivial_module():
    difference = pyff_module(TRIVIAL_MODULE, TRIVIAL_MODULE)
    assert difference is None

def test_changed_module():
    difference = pyff_module(TRIVIAL_MODULE, IMPORT_MODULE)
    assert difference is not None
    assert len(difference) == 1
    assert str(difference) == "Added import of new names ``path'' from new package ``os''"

def test_module_with_new_class():
    difference = pyff_module(TRIVIAL_MODULE, CLASSES_MODULE)
    assert difference is not None
    assert len(difference) == 1
    assert str(difference) == "New class ``Klass'' with 1 public methods"

def test_module_with_changed_function(): # pylint: disable=invalid-name
    difference = pyff_module(TRIVIAL_MODULE, CHANGED_FUNCTION_MODULE)
    assert difference is not None
    assert len(difference) == 1
    assert str(difference) == "Function ``func'' changed implementation"

def test_module_with_new_external_names_usage(): # pylint: disable=invalid-name
    difference = pyff_module(IMPORT_MODULE, IMPORT_USAGE_MODULE)
    assert difference is not None
    assert len(difference) == 1
    assert (str(difference) ==
            "Function ``func'' changed implementation, newly uses external names ``path''")
