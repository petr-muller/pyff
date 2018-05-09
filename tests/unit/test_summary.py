# pylint: disable=missing-docstring

from pytest import raises
from pyff.summary import ClassSummary, LocalBaseClass, ImportedBaseClass, FunctionSummary

def test_class_summary():
    cls = ClassSummary("classname", methods=5, private=2)
    assert cls.name == "classname"
    assert cls.methods == 5
    assert cls.private_methods == 2
    assert cls.public_methods == 3
    assert str(cls) == "class ``classname'' with 3 public methods"

def test_baseclasses():
    base = LocalBaseClass("Local")
    imported = ImportedBaseClass("ImportedClass")
    assert str(base) == "local ``Local''"
    assert str(imported) == "imported ``ImportedClass''"

def test_inherited_class_summary():
    local = ClassSummary("classname", methods=0, private=0,
                         baseclasses=[LocalBaseClass("LocalClass")])
    imported = ClassSummary("classname", methods=0, private=0,
                            baseclasses=[ImportedBaseClass("ImportedClass")])
    assert str(local) == "class ``classname'' derived from local ``LocalClass'' with 0 public methods" # pylint: disable=line-too-long
    assert str(imported) == "class ``classname'' derived from imported ``ImportedClass'' with 0 public methods" # pylint: disable=line-too-long

def test_multiple_inherited_summary():
    local = ClassSummary("classname", methods=0, private=0,
                         baseclasses=[LocalBaseClass("C1"), LocalBaseClass("C2")])
    with raises(Exception):
        str(local)

def test_function_summary():
    function = FunctionSummary('funktion')
    assert function.name == 'funktion'
    assert str(function) == "function ``funktion''"
