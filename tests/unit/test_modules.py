# pylint: disable=missing-docstring

from pyff.pyff import pyff_module

TRIVIAL_MODULE = """import sys
def func():
    pass"""

NEW_FUNCTION_MODULE = """import sys
def func():
    pass

def Funktion():
    pass
"""

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

EXTERNAL_INHERITANCE_CLASS_MODULE = """import sys
from module import BaseKlass

class Klass(BaseKlass):
    pass

class KildKlass(Klass):
    pass

def func():
    pass
"""

CHANGED_IMPORTS_MODULE = """import sys
import os
def func():
    return path()"""

def test_import_changes():
    difference = pyff_module(IMPORT_USAGE_MODULE, CHANGED_IMPORTS_MODULE)
    assert difference is not None
    assert str(difference) == "New imported package ``os'' (previously, only ``path'' was imported from ``os'')" # pylint: disable=line-too-long
    # assert str(difference) == "New imported package ``os'' (previously, only ``path'' were imported from ``os'')\nReferences of ``path'' were changed to ``os.path''" # pylint: disable=line-too-long

def test_trivial_module():
    difference = pyff_module(TRIVIAL_MODULE, TRIVIAL_MODULE)
    assert difference is None

def test_changed_module():
    difference = pyff_module(TRIVIAL_MODULE, IMPORT_MODULE)
    assert difference is not None
    assert str(difference) == "New imported names ``path'' from new package ``os''"

def test_module_with_new_class():
    difference = pyff_module(TRIVIAL_MODULE, CLASSES_MODULE)
    assert difference is not None
    assert str(difference) == "New class ``Klass'' with 1 public methods"

def test_module_with_new_function():
    difference = pyff_module(TRIVIAL_MODULE, NEW_FUNCTION_MODULE)
    assert difference is not None
    assert str(difference) == "New function ``Funktion''"

def test_module_with_inherited_classes(): # pylint: disable=invalid-name
    difference = pyff_module(TRIVIAL_MODULE, EXTERNAL_INHERITANCE_CLASS_MODULE)
    assert difference is not None
    assert (sorted(str(difference).split('\n')) ==
            ["New class ``KildKlass'' derived from local ``Klass'' with 0 public methods",
             "New class ``Klass'' derived from imported ``BaseKlass'' with 0 public methods",
             "New imported names ``BaseKlass'' from new package ``module''"])

def test_module_with_changed_function(): # pylint: disable=invalid-name
    difference = pyff_module(TRIVIAL_MODULE, CHANGED_FUNCTION_MODULE)
    assert difference is not None
    assert str(difference) == "Function ``func'' changed implementation"

def test_module_with_new_external_names_usage(): # pylint: disable=invalid-name
    difference = pyff_module(IMPORT_MODULE, IMPORT_USAGE_MODULE)
    assert difference is not None
    assert (str(difference) ==
            "Function ``func'' changed implementation, newly uses external names ``path''")
