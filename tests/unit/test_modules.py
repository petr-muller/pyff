# pylint: disable=missing-docstring, no-self-use, too-few-public-methods

import ast

import pyff.modules as pm
import pyff.imports as pi
import pyff.functions as pf
import pyff.classes as pc

from helpers import parse_imports


class TestModulePyfference:
    def test_sanity(self):
        old = parse_imports("import four; from five import six, seven")
        new = parse_imports(
            "import one, two, three; "
            "from module import fst, snd; "
            "from five import seven; "
            "from eight import nine"
        )
        imports = pi.ImportedNames.compare(old, new)
        functions = pf.FunctionsPyfference(
            new={pf.FunctionSummary("function"), pf.FunctionSummary("funktion")},
            changed={
                "name": pf.FunctionPyfference("name", old_name="old_name", implementation=set())
            },
        )
        classes = pc.ClassesPyfference(new={"NewClass2", "NewClass"})
        change = pm.ModulePyfference(imports, classes, functions)
        assert change.classes is not None
        assert change.functions is not None
        assert change.imports is not None
        assert str(change) == (
            "Removed import of package ``four''\n"
            "New imported packages ``one'', ``three'', ``two''\n"
            "Removed import of ``six'' from ``five''\n"
            "New imported ``fst'', ``snd'' from new ``module''\n"
            "New imported ``nine'' from new ``eight''\n"
            "New NewClass\n"
            "New NewClass2\n"
            "New function ``function''\n"
            "New function ``funktion''\n"
            "Function ``old_name'' renamed to ``name''"
        )
        assert change.simplify() is change

    def test_empty(self):
        change = pm.ModulePyfference()
        assert change.simplify() is None


class TestPyffModule:
    def test_sanity(self):
        old = ast.parse("")
        new = ast.parse("import os\n" "class Klass:\n" "    pass\n" "def funktion():\n" "    pass")
        change = pm.pyff_module(old, new)
        assert change.imports is not None
        assert change.classes is not None
        assert change.functions is not None

    def test_same(self):
        module = ast.parse(
            "import os\n" "class Klass:\n" "    pass\n" "def funktion():\n" "    pass"
        )
        assert pm.pyff_module(module, module) is None


class TestPyffModuleCode:
    def test_sanity(self):
        old = ""
        new = "import os\n" "class Klass:\n" "    pass\n" "def funktion():\n" "    pass"
        change = pm.pyff_module_code(old, new)
        assert change.imports is not None
        assert change.classes is not None
        assert change.functions is not None
