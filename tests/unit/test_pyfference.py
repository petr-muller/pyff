# pylint: disable=missing-docstring

import pyff.pyfference as pf

def test_function_name_changed():
    fpyff = pf.FunctionPyfference(names=("first", "second"))
    assert fpyff.name.old == "first"
    assert fpyff.name.new == "second"
    assert len(fpyff) == 1

def test_function_name_same():
    fpyff = pf.FunctionPyfference()
    assert fpyff.name is None
    assert len(fpyff) == 0  # pylint: disable=len-as-condition

def test_new_from_import():
    mpyff = pf.FromImportPyfference(new={'os': ['path', 'getenv']})
    assert mpyff.new == {'os': ['path', 'getenv']}
    assert str(mpyff) == "Added import of new names 'path', 'getenv' from new package 'os'"

def test_module_with_from_imports():
    fip = pf.FromImportPyfference(new={'os': ['path', 'getenv']})
    mpyff = pf.ModulePyfference(from_imports=fip)
    assert mpyff.from_imports is not None
    assert len(mpyff) == 1
    assert str(mpyff) == "Added import of new names 'path', 'getenv' from new package 'os'"

def test_new_classes():
    cpyff = pf.ClassesPyfference(new=["NewClass", "NewClass2"])
    assert cpyff.new == ["NewClass", "NewClass2"]
    assert str(cpyff) == "New class 'NewClass'\nNew class 'NewClass2'"

def test_module_with_new_classes():
    cpyff = pf.ClassesPyfference(new=["NewClass"])
    mpyff = pf.ModulePyfference(classes=cpyff)
    assert mpyff.classes is not None
    assert len(mpyff) == 1
    assert str(mpyff) == "New class 'NewClass'"
