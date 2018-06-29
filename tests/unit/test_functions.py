# pylint: disable=missing-docstring, no-self-use, too-few-public-methods

import ast
from unittest.mock import Mock
import pytest
import pyff.functions as pf
import pyff.imports as pi
import pyff.statements as ps

from helpers import parse_imports, extract_names_from_function


class TestFunctionImplementationChange:
    def test_sanity(self):
        fic = pf.FunctionImplementationChange()
        assert fic is not None

    def test_make_message(self):
        fic = pf.FunctionImplementationChange()
        assert fic.make_message() == "Code semantics changed"

    def test_equality(self):
        assert pf.FunctionImplementationChange() == pf.FunctionImplementationChange()
        a_set = {pf.FunctionImplementationChange()}
        a_set.add(pf.FunctionImplementationChange())
        assert len(a_set) == 1


class TestExternalUsageChange:
    def test_sanity(self):
        euc = pf.ExternalUsageChange(gone={"name", "another_name"}, appeared={"new_name"})
        assert euc.gone == {"another_name", "name"}
        assert euc.appeared == {"new_name"}

    def test_make_message(self):
        euc = pf.ExternalUsageChange(gone={"name", "another_name"}, appeared={"new_name"})
        assert (
            euc.make_message() == "No longer uses imported ``another_name'', ``name''\n"
            "Newly uses imported ``new_name''"
        )

    def test_equality(self):
        euc = pf.ExternalUsageChange(gone={"name", "another_name"}, appeared={"new_name"})
        euc_same = pf.ExternalUsageChange(gone={"another_name", "name"}, appeared={"new_name"})
        euc_diff = pf.ExternalUsageChange(gone={"name"}, appeared={"new_name"})

        assert euc == euc_same
        assert euc != euc_diff


class TestStatementChange:
    def test_sanity(self):
        spyff = ps.StatementPyfference()
        change = pf.StatementChange(spyff)

        assert change.make_message() == str(spyff)


class TestFunctionPyfferenceRecorder:
    def test_nochange(self):
        recorder = pf.FunctionPyfferenceRecorder("function_name")
        assert recorder.build() is None

    def test_namechange(self):
        recorder = pf.FunctionPyfferenceRecorder("function_name")
        recorder.name_changed("old_name")
        pyfference = recorder.build()
        assert pyfference.name == "function_name"
        assert pyfference.old_name == "old_name"
        assert not pyfference.implementation

    def test_implementation(self):
        recorder = pf.FunctionPyfferenceRecorder("function_name")
        recorder.implementation_changed(pf.FunctionImplementationChange())
        pyfference = recorder.build()
        assert pyfference.old_name is None
        assert len(pyfference.implementation) == 1


class TestFunctionPyfference:
    def test_sanity(self):  # pylint: disable=invalid-name
        fic = pf.FunctionImplementationChange()
        fp1 = pf.FunctionPyfference(name="function", implementation={fic}, old_name="old_function")
        assert fp1.name == "function"
        assert fp1.implementation == {fic}
        assert fp1.old_name == "old_function"

        fp2 = pf.FunctionPyfference(name="function", implementation={fic})
        assert fp2.name == "function"
        assert fp2.implementation == {fic}
        assert fp2.old_name is None

    def test_name_change(self):
        change = pf.FunctionPyfference(name="function", implementation=set(), old_name="funktion")
        assert str(change) == "Function ``funktion'' renamed to ``function''"

    def test_method_name_change(self):
        change = pf.FunctionPyfference(name="function", implementation=set(), old_name="funktion")
        change.set_method()
        assert str(change) == "Method ``funktion'' renamed to ``function''"

    def test_implementation_change(self):
        fic = pf.FunctionImplementationChange()
        change = pf.FunctionPyfference(name="function", implementation={fic})
        assert (
            str(change) == "Function ``function'' changed implementation:\n"
            "  Code semantics changed"
        )

    def test_simplify(self):
        fic = pf.FunctionImplementationChange()
        change = pf.FunctionPyfference(name="function", implementation={fic})
        assert change.simplify() is change

        empty_change = pf.FunctionPyfference(name="function", implementation=set())
        assert empty_change.simplify() is None

        name_change = pf.FunctionPyfference(
            name="function", implementation=set(), old_name="funktion"
        )
        assert name_change.simplify() is name_change


class TestExternalNamesExtractor:
    def test_import(self):
        imported_names = parse_imports("import package, pkg.module, something as alias")
        package_names = extract_names_from_function(
            "def function(): a = package.function()", imported_names
        )
        assert package_names == {"package"}

        module_names = extract_names_from_function(
            "def function(): a = pkg.module.attribute + 3", imported_names
        )
        assert module_names == {"pkg.module"}

        alias_names = extract_names_from_function(
            "def f(): a = alias.C().package + pkg.module.p", imported_names
        )
        assert alias_names == {"alias", "pkg.module"}

    def test_importfrom(self):
        imported_names = parse_imports(
            "from pk import name, other as alias; " "from pk.mod import other"
        )
        package_names = extract_names_from_function("def function(): a = name()", imported_names)
        assert package_names == {"name"}

        alias_names = extract_names_from_function("def function(): a = alias + 3", imported_names)
        assert alias_names == {"alias"}

        module_names = extract_names_from_function(
            "def function(): a = other(3) + pkg + mod", imported_names
        )
        assert module_names == {"other"}


class TestCompareImportUsage:
    def test_no_external(self):
        old_imports = parse_imports("import os; from ast import Name; import sys as system")
        new_imports = parse_imports("from os import path; import unittest")

        old_function = ast.parse("def function(a, b, c): return a if b else c")
        new_function = ast.parse("def function(a, b, c): temp = a / c; return temp if b else None")

        assert pf.compare_import_usage(old_function, new_function, old_imports, new_imports) is None

    def test_appeared(self):
        old_imports = parse_imports("import os; from ast import Name; import sys as system")
        new_imports = parse_imports("import os; import unit")

        old_function = ast.parse("def function(a, b, c): return os.path.join([a, b, c])")
        new_function = ast.parse(
            "def function(a, b, c): unit.method(); return os.path.join([a,b,c])"
        )

        change = pf.compare_import_usage(old_function, new_function, old_imports, new_imports)
        assert change.appeared == {"unit"}

    def test_gone(self):
        old_imports = parse_imports("import os; from ast import Name; import sys as system")
        new_imports = parse_imports("from os.path import join; import unittest")

        old_function = ast.parse("def function(a, b, c): return os.path.join([a, b, c])")
        new_function = ast.parse("def function(a, b, c): return join([a, b, c])")

        change = pf.compare_import_usage(old_function, new_function, old_imports, new_imports)
        assert change.appeared == {"join"}
        assert change.gone == {"os"}


class TestPyffFunction:
    @staticmethod
    def _make_summary(code: str):
        extractor = pf.FunctionsExtractor()
        extractor.visit(ast.parse(code))
        return extractor.functions.popitem()[1]

    def test_identical(self):
        # ast.parse gives us ast.Module
        old = self._make_summary("def function(): return os.path.join(lst)")
        new = self._make_summary("def function(): return os.path.join(lst)")

        assert pf.pyff_function(old, new, pi.ImportedNames(), pi.ImportedNames()) is None

    def test_namechange(self):
        # ast.parse gives us ast.Module
        old = self._make_summary("def function(): return os.path.join(lst)")
        new = self._make_summary("def funktion(): return os.path.join(lst)")

        pyfference = pf.pyff_function(old, new, pi.ImportedNames(), pi.ImportedNames())
        assert pyfference.name == "funktion"
        assert pyfference.old_name == "function"

    def test_imports_fixes(self):
        old = self._make_summary("def function(): return path.join(lst)")
        new = self._make_summary("def function(): return pathy.join(lst)")
        old_imports = parse_imports("from os import path")
        new_imports = parse_imports("from os import path as pathy")

        pyfference = pf.pyff_function(old, new, old_imports, new_imports)
        assert len(pyfference.implementation) == 2

    def test_external_name_usage(self):
        old = self._make_summary("def function(): return some_path")
        new = self._make_summary("def function(): return pathy.join(lst)")
        old_imports = parse_imports("from os import path")
        new_imports = parse_imports("from os import path as pathy")

        pyfference = pf.pyff_function(old, new, old_imports, new_imports)
        assert len(pyfference.implementation) == 2

    def test_different_statement_count(self):
        old = self._make_summary("def function(): do_some_useless_stuff();")
        new = self._make_summary("def function(): do_some_useless_stuff(); return None")
        no_imports = parse_imports("")

        pyfference = pf.pyff_function(old, new, no_imports, no_imports)
        assert len(pyfference.implementation) == 1


class TestPyffFunctionCode:

    FUNCTION = "def function(): return os.path.join(lst)"
    FUNKTION = "def funktion(): return os.path.join(lst)"
    KLASS = "class Klass: pass"

    def test_identical(self):
        assert (
            pf.pyff_function_code(
                self.FUNCTION, self.FUNCTION, pi.ImportedNames(), pi.ImportedNames()
            )
            is None
        )

    def test_namechange(self):
        pyfference = pf.pyff_function_code(
            self.FUNCTION, self.FUNKTION, pi.ImportedNames(), pi.ImportedNames()
        )
        assert pyfference.name == "funktion"
        assert pyfference.old_name == "function"

    def test_invalid(self):
        with pytest.raises(ValueError):
            pf.pyff_function_code(self.FUNCTION, self.KLASS, pi.ImportedNames(), pi.ImportedNames())

        with pytest.raises(ValueError):
            pf.pyff_function_code(self.KLASS, self.FUNKTION, pi.ImportedNames(), pi.ImportedNames())


class TestFunctionSummary:
    @pytest.fixture
    def mocked_node(self):
        return Mock(spec=ast.FunctionDef)

    def test_sanity(self, mocked_node):
        summary = pf.FunctionSummary("funktion", node=mocked_node)
        assert summary.name == "funktion"
        assert summary == pf.FunctionSummary("funktion", node=mocked_node)
        assert summary != pf.FunctionSummary("function", node=mocked_node)
        assert str(summary) == "function ``funktion''"

    def test_set_method(self, mocked_node):
        summary = pf.FunctionSummary("funktion", node=mocked_node)
        summary.set_method()
        assert str(summary) == "method ``funktion''"

    def test_property(self, mocked_node):
        noprop = pf.FunctionSummary("funktion", node=mocked_node)
        assert not noprop.property
        prop = pf.FunctionSummary("funktion", is_property=True, node=mocked_node)
        assert prop.property
        assert str(prop) == "property function ``funktion''"


class TestFunctionsExtractor:
    @pytest.fixture
    def extractor(self):
        return pf.FunctionsExtractor()

    def test_functions(self, extractor):
        extractor.visit(
            ast.parse("def funktion_one():\n" "    pass\n" "def funktion_two():\n" "    pass\n")
        )
        assert extractor.names == {"funktion_one", "funktion_two"}
        assert "funktion_one" in extractor.functions
        assert "funktion_two" in extractor.functions

    def test_not_enter_classes(self, extractor):
        extractor.visit(
            ast.parse(
                "def funktion():\n"
                "    pass\n"
                "class Klass:\n"
                "    def method(self):\n"
                "        pass"
            )
        )
        assert extractor.names == {"funktion"}
        assert "method" not in extractor.functions

    def test_property_functions(self, extractor):
        extractor.visit(ast.parse("@property\ndef prop(): pass"))
        assert str(extractor.functions["prop"]) == "property function ``prop''"


class TestFunctionsPyfference:
    def test_sanity(self):
        mocked_node = Mock(spec=ast.FunctionDef)
        new = {
            "function": pf.FunctionSummary("function", node=mocked_node),
            "funktion": pf.FunctionSummary("funktion", node=mocked_node),
        }
        changed = {
            "another": pf.FunctionPyfference(
                "another", old_name="old_another", implementation=set()
            )
        }
        removed = {
            "gone": pf.FunctionSummary("gone", node=mocked_node),
            "for_good": pf.FunctionSummary("for_good", node=mocked_node),
        }
        change = pf.FunctionsPyfference(new=new, changed=changed, removed=removed)
        assert change.new["function"] == pf.FunctionSummary("function", node=mocked_node)
        assert change.new["funktion"] == pf.FunctionSummary("funktion", node=mocked_node)
        assert change.removed["gone"] == pf.FunctionSummary("gone", node=mocked_node)
        assert change.removed["for_good"] == pf.FunctionSummary("for_good", node=mocked_node)
        assert change.changed["another"].old_name == "old_another"
        assert str(change) == (
            "Removed function ``for_good''\n"
            "Removed function ``gone''\n"
            "Function ``old_another'' renamed to ``another''\n"
            "New function ``function''\n"
            "New function ``funktion''"
        )
        change.set_method()
        assert str(change) == (
            "Removed method ``for_good''\n"
            "Removed method ``gone''\n"
            "Method ``old_another'' renamed to ``another''\n"
            "New method ``function''\n"
            "New method ``funktion''"
        )


class TestPyffFunctions:
    def test_sanity(self):
        old = ast.parse(
            "def same_funktion():\n" "   pass\n" "def changed_funktion():\n" "   pass\n"
        )
        new = ast.parse(
            "def same_funktion():\n"
            "   pass\n"
            "def changed_funktion():\n"
            "   return None\n"
            "def new_funktion():\n"
            "   pass"
        )
        old_imports = pi.ImportedNames.extract(old)
        new_imports = pi.ImportedNames.extract(new)
        change = pf.pyff_functions(old, new, old_imports, new_imports)
        assert change is not None
        assert len(change.new) == 1
        new_funktion = change.new["new_funktion"]
        assert new_funktion.name == "new_funktion"

        assert len(change.changed) == 1
        assert "changed_funktion" in change.changed

    def test_property_functions(self):
        no_method = ast.parse("")
        property_method = ast.parse("@property\ndef property_method(): pass")
        no_imports = pi.ImportedNames.extract(no_method)

        assert (
            str(pf.pyff_functions(no_method, property_method, no_imports, no_imports))
            == "New property function ``property_method''"
        )
        assert (
            str(pf.pyff_functions(property_method, no_method, no_imports, no_imports))
            == "Removed property function ``property_method''"
        )

    def test_changed_arguments(self):
        old = ast.parse(
            "import pathlib\n"
            "def funktion(arg: pathlib.Path) -> pathlib.Path:\n"
            "   return GLOBAL / arg"
        )
        new = ast.parse(
            "from pathlib import Path\n"
            "def funktion(arg: Path) -> Path:\n"
            "   return GLOBAL / arg"
        )
        old_imports = pi.ImportedNames.extract(old)
        new_imports = pi.ImportedNames.extract(new)
        change = pf.pyff_functions(old, new, old_imports, new_imports)
        # right now, we do not detect different type hints
        assert change is None

    def test_same(self):
        module = ast.parse(
            "def same_funktion():\n" "   pass\n" "def changed_funktion():\n" "   pass\n"
        )
        imports = pi.ImportedNames.extract(module)
        assert pf.pyff_functions(module, module, imports, imports) is None
