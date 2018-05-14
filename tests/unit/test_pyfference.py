# pylint: disable=missing-docstring

import pyff.pyfference as pf

def test_function_name_changed():
    fpyff = pf.FunctionPyfference(name="first", names=("first", "second"))
    assert fpyff.name == "first"
    assert fpyff.names.old == "first"
    assert fpyff.names.new == "second"
    assert fpyff.implementation is None
    assert str(fpyff) == "Function ``first'' renamed to ``second''"

def test_function_same():
    fpyff = pf.FunctionPyfference(name="func")
    assert fpyff.name == "func"
    assert fpyff.names is None
    assert fpyff.implementation is None
    assert str(fpyff) == ""

def test_function_implementation_changed(): # pylint: disable=invalid-name
    fpyff = pf.FunctionPyfference(name="func", implementation=True)
    assert fpyff.name == "func"
    assert fpyff.names is None
    assert fpyff.implementation is True
    assert str(fpyff) == "Function ``func'' changed implementation"

def test_function_everything_changed(): # pylint: disable=invalid-name
    fpyff = pf.FunctionPyfference(name="first", names=("first", "second"), implementation=True)
    assert str(fpyff) == "Function ``first'' renamed to ``second'' and its implementation changed"

def test_new_from_import():
    mpyff = pf.FromImportPyfference(new={'os': ['path', 'getenv']}, removed={})
    assert mpyff.new == {'os': ['path', 'getenv']}
    assert str(mpyff) == "New imported names ``getenv'', ``path'' from new package ``os''"

def test_from_import_removed():
    fipyff = pf.FromImportPyfference(removed={'os': ['path']}, new={})
    assert fipyff.removed == {'os': ['path']}
    assert str(fipyff) == "Removed import of names ``path'' from package ``os''"

def test_imports():
    ipyff = pf.ImportPyfference(new={'os', 'sys'}, removed={'unittest'})
    assert ipyff.new == {'os', 'sys'}
    assert ipyff.removed == {'unittest'}
    assert str(ipyff) == "Removed import of packages ``unittest''\nNew imported packages ``os'', ``sys''" # pylint: disable=line-too-long

def test_module_with_from_imports():
    fip = pf.FromImportPyfference(new={'os': ['path', 'getenv']}, removed={})
    mpyff = pf.ModulePyfference(from_imports=fip)
    assert mpyff.from_imports is not None
    assert str(mpyff) == "New imported names ``getenv'', ``path'' from new package ``os''"

def test_new_classes():
    cpyff = pf.ClassesPyfference(new={"NewClass", "NewClass2"})
    assert cpyff.new == {"NewClass", "NewClass2"}
    assert str(cpyff) == "New NewClass\nNew NewClass2"

def test_module_with_new_classes():
    cpyff = pf.ClassesPyfference(new=["NewClass", "NewClass2"])
    mpyff = pf.ModulePyfference(classes=cpyff)
    assert mpyff.classes is not None
    assert str(mpyff) == "New NewClass\nNew NewClass2"

def test_function_new():
    fpyff = pf.FunctionsPyfference(new=("NewFunktion", "AnotherNewFunktion"), changed={})
    assert fpyff.new == ("NewFunktion", "AnotherNewFunktion")
    assert str(fpyff) == "New AnotherNewFunktion\nNew NewFunktion"
    mpyff = pf.ModulePyfference(functions=fpyff)
    assert mpyff.functions is not None
    assert str(mpyff) == "New AnotherNewFunktion\nNew NewFunktion"

def test_functions_changed():
    fpyff = pf.FunctionPyfference(name='func', implementation=True)
    fspyff = pf.FunctionsPyfference(changed={'func': fpyff}, new=set())
    assert fspyff.changed is not None
    assert str(fspyff) == "Function ``func'' changed implementation"

def test_module_with_changed_functions(): # pylint: disable=invalid-name
    fpyff = pf.FunctionPyfference(name='func', implementation=True)
    fspyff = pf.FunctionsPyfference(changed={'func': fpyff}, new=set())
    mpyff = pf.ModulePyfference(functions=fspyff)
    assert mpyff.functions is not None
    assert str(mpyff) == "Function ``func'' changed implementation"
