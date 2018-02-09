# pylint: disable=missing-docstring

from pyff.pyfference import FunctionPyfference, FromImportPyfference, ModulePyfference

def test_function_name_changed():
    fpyff = FunctionPyfference(names=("first", "second"))
    assert fpyff.name.old == "first"
    assert fpyff.name.new == "second"
    assert len(fpyff) == 1

def test_function_name_same():
    fpyff = FunctionPyfference()
    assert fpyff.name is None
    assert len(fpyff) == 0  # pylint: disable=len-as-condition

def test_new_from_import():
    mpyff = FromImportPyfference(new={'os': ['path', 'getenv']})
    assert mpyff.new == {'os': ['path', 'getenv']}
    assert str(mpyff) == "Added import of new names 'path', 'getenv' from new package 'os'"

def test_module_with_from_imports():
    mpyff = ModulePyfference(from_imports=FromImportPyfference(new={'os': ['path', 'getenv']}))
    assert mpyff.from_imports is not None
    assert len(mpyff) == 1
    assert str(mpyff) == "Added import of new names 'path', 'getenv' from new package 'os'"
