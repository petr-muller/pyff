# pylint: disable=missing-docstring, no-self-use, too-few-public-methods

import ast
import pytest
import pyff.imports as pi
from helpers import parse_imports


class TestImportedName:
    def test_import(self):
        alias = ast.alias(name="os.path", asname=None)
        name = pi.ImportedName("os.path", ast.Import(names=[alias]), alias)
        assert name.name == "os.path"
        assert name.node.names[0].name == "os.path"
        assert name.node.names[0].asname is None
        assert name.alias is alias
        assert name.is_import()
        assert not name.is_import_from()

    def test_importfrom(self):
        alias = ast.alias(name="path", asname=None)
        name = pi.ImportedName("path", ast.ImportFrom(module="os", level=0, names=[alias]), alias)
        assert name.name == "path"
        assert name.node.module == "os"
        assert name.node.names[0].name == "path"
        assert name.node.names[0].asname is None
        assert name.node.level == 0
        assert name.alias is alias
        assert not name.is_import()
        assert name.is_import_from()

    def test_fqdn_imports(self):
        simple = ast.alias(name="os", asname=None)
        assert pi.ImportedName("os", ast.Import(names=[simple]), simple).canonical_name == "os"

        module = ast.alias(name="os.path", asname=None)
        module_name = pi.ImportedName("os.path", ast.Import(names=[module]), module)
        assert module_name.canonical_name == "os.path"

        alias = ast.alias(name="os.path", asname="path")
        assert pi.ImportedName("path", ast.Import(names=[alias]), alias).canonical_name == "os.path"

    def test_fqast_imports(self):
        simple = ast.alias(name="os", asname=None)
        node_ast = ast.dump(pi.ImportedName("os", ast.Import(names=[simple]), simple).canonical_ast)
        assert node_ast == "Name(id='os', ctx=Load())"

        module = ast.alias(name="os.path", asname=None)
        module_name = pi.ImportedName("os.path", ast.Import(names=[module]), module)
        module_ast = ast.dump(module_name.canonical_ast)
        assert module_ast == "Attribute(value=Name(id='os', ctx=Load()), attr='path', ctx=Load())"

        alias = ast.alias(name="os.path", asname="path")
        alias_ast = ast.dump(
            pi.ImportedName("path", ast.Import(names=[alias]), alias).canonical_ast
        )
        assert alias_ast == "Attribute(value=Name(id='os', ctx=Load()), attr='path', ctx=Load())"

    def test_fqdn_importfrom(self):
        # 'from os import path'
        simple = ast.alias(name="path", asname=None)
        simple_name = ast.ImportFrom(module="os", names=[simple])
        assert pi.ImportedName("path", simple_name, simple).canonical_name == "os.path"

        module = ast.alias(name="four", asname=None)
        module_name = ast.ImportFrom(module="one.two.three", names=[module])
        assert pi.ImportedName("four", module_name, module).canonical_name == "one.two.three.four"

        alias = ast.alias(name="fourth_module", asname="four")
        alias_name = ast.ImportFrom(module="one.two.three", names=[alias])
        assert (
            pi.ImportedName("four", alias_name, alias).canonical_name
            == "one.two.three.fourth_module"
        )

    def test_fqast_importfrom(self):
        simple = ast.alias(name="path", asname=None)
        simple_name = pi.ImportedName("path", ast.ImportFrom(module="os", names=[simple]), simple)
        simple_ast = ast.dump(simple_name.canonical_ast)
        assert simple_ast == "Attribute(value=Name(id='os', ctx=Load()), attr='path', ctx=Load())"

        module = ast.alias(name="four", asname=None)
        module_node = ast.ImportFrom(module="one.two.three", names=[module])
        module_name = pi.ImportedName("four", module_node, module)
        module_ast = ast.dump(module_name.canonical_ast)
        assert (
            module_ast
            == "Attribute(value=Attribute(value=Attribute(value=Name(id='one', ctx=Load()), attr='two', ctx=Load()), attr='three', ctx=Load()), attr='four', ctx=Load())"  # pylint: disable=line-too-long
        )

        alias = ast.alias(name="fourth_module", asname="four")
        alias_node = ast.ImportFrom(module="one.two.three", names=[alias])
        alias_name = pi.ImportedName("four", alias_node, alias)
        alias_ast = ast.dump(alias_name.canonical_ast)
        assert (
            alias_ast
            == "Attribute(value=Attribute(value=Attribute(value=Name(id='one', ctx=Load()), attr='two', ctx=Load()), attr='three', ctx=Load()), attr='fourth_module', ctx=Load())"  # pylint: disable=line-too-long
        )


class TestImportedNames:
    def test_dictionary(self):
        names = pi.ImportedNames()
        assert not names

        names.add_import(ast.Import(names=[ast.alias(name="os", asname=None)]))
        assert len(names) == 1
        assert "os" in names
        assert names["os"].name == "os"
        assert len(names["os"].node.names) == 1

        assert list(sorted(names)) == ["os"]

    def test_import(self):
        names = pi.ImportedNames()
        names.add_import(
            ast.Import(
                names=[ast.alias(name="os", asname=None), ast.alias(name="sys", asname=None)]
            )
        )
        names.add_import(ast.Import(names=[ast.alias(name="ast", asname=None)]))
        assert len(names) == 3
        assert "os" in names
        assert "sys" in names
        assert "ast" in names

        assert names["os"].node is names["sys"].node
        assert names["os"].node is not names["ast"].node

    def test_importfrom(self):
        names = pi.ImportedNames()
        names.add_importfrom(
            ast.ImportFrom(
                module="os",
                level=0,
                names=[ast.alias(name="path", asname=None), ast.alias(name="environ", asname=None)],
            )
        )
        names.add_importfrom(
            ast.ImportFrom(module="sys", level=0, names=[ast.alias(name="exit", asname=None)])
        )
        assert len(names) == 3
        assert "path" in names
        assert "environ" in names
        assert "exit" in names
        assert names["path"].node is names["environ"].node
        assert names["exit"].node is not names["path"].node
        assert names.from_modules == {"os", "sys"}

    def test_asname(self):
        names = pi.ImportedNames()
        names.add_import(ast.Import(names=[ast.alias(name="os.environ", asname="oe")]))
        assert len(names) == 1
        assert "oe" in names


class TestPyffImports:
    def test_new_import(self):
        old = ""
        new = "import os"

        assert len(pi.pyff_imports_code(old, new).new_imports) == 1
        assert len(pi.pyff_imports(ast.parse(old), ast.parse(new)).new_imports) == 1
        assert pi.pyff_imports_code(new, new) is None
        assert pi.pyff_imports(ast.parse(new), ast.parse(new)) is None


class TestImportedNamesCompare:
    def test_new_import(self):
        old = parse_imports("import os")
        new = parse_imports("import os; import sys")
        new_with_comma = parse_imports("import os, sys")

        change = pi.ImportedNames.compare(old, new)
        assert len(change.new_imports) == 1
        assert max(change.new_imports).canonical_name == "sys"

        change_with_comma = pi.ImportedNames.compare(old, new_with_comma)
        assert len(change_with_comma.new_imports) == 1
        assert max(change_with_comma.new_imports).canonical_name == "sys"

    def test_removed_import(self):
        old = parse_imports("import os; import sys")
        old_with_comma = parse_imports("import os, sys")
        new = parse_imports("import os")

        change = pi.ImportedNames.compare(old, new)
        assert len(change.removed_imports) == 1
        assert max(change.removed_imports).canonical_name == "sys"

        change = pi.ImportedNames.compare(old_with_comma, new)
        assert len(change.removed_imports) == 1
        assert max(change.removed_imports).canonical_name == "sys"

    def test_new_importfrom(self):
        old = parse_imports("from os import path")
        new = parse_imports("from os import path; from os import environ")
        new_with_comma = parse_imports("from os import path, environ")

        change = pi.ImportedNames.compare(old, new)
        assert len(change.fromimports.new) == 1
        assert not change.fromimports.new_modules
        assert change.fromimports.new["os"].pop().canonical_name == "os.environ"

        change_with_comma = pi.ImportedNames.compare(old, new_with_comma)
        assert len(change_with_comma.fromimports.new) == 1
        assert not change.fromimports.new_modules
        assert change_with_comma.fromimports.new["os"].pop().canonical_name == "os.environ"

    def test_removed_importfrom(self):
        old = parse_imports("from os import path; from os import environ")
        old_with_comma = parse_imports("from os import path, environ")
        new = parse_imports("from os import path")

        change = pi.ImportedNames.compare(old, new)
        assert len(change.fromimports.removed) == 1
        assert not change.fromimports.removed_modules
        assert change.fromimports.removed["os"].pop().canonical_name == "os.environ"

        change_with_comma = pi.ImportedNames.compare(old_with_comma, new)
        assert len(change_with_comma.fromimports.removed) == 1
        assert not change.fromimports.removed_modules
        assert change_with_comma.fromimports.removed["os"].pop().canonical_name == "os.environ"

    def test_new_importfrom_module(self):
        old = parse_imports("from os import path")
        new = parse_imports("from module import name")

        change = pi.ImportedNames.compare(old, new)
        assert len(change.fromimports.new) == 1
        assert len(change.fromimports.new_modules) == 1
        assert change.fromimports.new_modules == {"module"}

    def test_identical(self):
        old = parse_imports("from os import path")
        new = parse_imports("from os import path")

        assert pi.ImportedNames.compare(old, new) is None


class TestFromImportPyfference:
    @staticmethod
    @pytest.fixture
    def change():
        return pi.FromImportPyfference()

    def test_truthiness(self, change):
        assert not change
        change.add_new_modules({"w00t"})
        assert change

    def test_new(self, change):
        alias = ast.alias(name="path", asname=None)
        change.add_new(
            pi.ImportedName("path", ast.ImportFrom(module="os", level=0, names=[alias]), alias)
        )
        assert change.new["os"] is not None

    def test_removed(self, change):
        alias = ast.alias(name="path", asname=None)
        change.add_removed(
            pi.ImportedName("path", ast.ImportFrom(module="os", level=0, names=[alias]), alias)
        )
        assert change.removed["os"] is not None

    def test_new_modules(self, change):
        change.add_new_modules({"os", "awsum"})
        alias = ast.alias(name="path", asname=None)
        change.add_new(
            pi.ImportedName("path", ast.ImportFrom(module="os", level=0, names=[alias]), alias)
        )
        assert change.new_modules == {"awsum", "os"}
        assert change.new
        change.delete_new_module("os")
        assert change.new_modules == {"awsum"}
        assert not change.new

    def test_removed_modules(self, change):
        change.add_removed_modules({"w00t", "awsum"})
        assert change.removed_modules == {"awsum", "w00t"}
        change.delete_removed_module("w00t")
        assert change.removed_modules == {"awsum"}


class TestImportsPyfference:
    def test_truthiness(self):
        change = pi.ImportsPyfference()
        assert not change
        change.new_fromimport_modules({"w00t"})
        assert change

    def test_message_new_import(self):
        old = parse_imports("")
        new_one = parse_imports("import one")
        new_more = parse_imports("import one, two")
        assert str(pi.ImportedNames.compare(old, new_one)) == "New imported package ``one''"
        assert (
            str(pi.ImportedNames.compare(old, new_more)) == "New imported packages ``one'', ``two''"
        )

    def test_message_remove_import(self):
        old = parse_imports("import one, two")
        new_one = parse_imports("import one")
        new_more = parse_imports("")

        assert str(pi.ImportedNames.compare(old, new_one)) == "Removed import of package ``two''"
        assert (
            str(pi.ImportedNames.compare(old, new_more))
            == "Removed import of packages ``one'', ``two''"
        )  # pylint: disable=line-too-long

    def test_message_new_fromimport(self):
        old = parse_imports("from module import one")
        new_one = parse_imports("from module import one, two")
        new_more = parse_imports("from module import one, two, three")
        assert str(pi.ImportedNames.compare(old, new_one)) == "New imported ``two'' from ``module''"
        assert (
            str(pi.ImportedNames.compare(old, new_more))
            == "New imported ``three'', ``two'' from ``module''"
        )

    def test_message_remove_fromimport(self):
        old = parse_imports("from module import one, two, three")
        new_one = parse_imports("from module import one, two")
        new_more = parse_imports("from module import one")
        assert (
            str(pi.ImportedNames.compare(old, new_one))
            == "Removed import of ``three'' from ``module''"
        )
        assert (
            str(pi.ImportedNames.compare(old, new_more))
            == "Removed import of ``three'', ``two'' from ``module''"
        )

    def test_message_new_fromimport_module(self):  # pylint: disable=invalid-name
        old = parse_imports("")
        new_one = parse_imports("from module import one")
        new_more = parse_imports("from module import one, two")
        assert (
            str(pi.ImportedNames.compare(old, new_one))
            == "New imported ``one'' from new ``module''"
        )
        assert (
            str(pi.ImportedNames.compare(old, new_more))
            == "New imported ``one'', ``two'' from new ``module''"
        )

    def test_message_removed_fromimport_module(self):  # pylint: disable=invalid-name
        old = parse_imports("from module import one")
        new = parse_imports("")
        assert (
            str(pi.ImportedNames.compare(old, new))
            == "Removed import of ``one'' from removed ``module''"
        )

    def test_from_to_general(self):
        old = parse_imports("from pathlib import Path")
        new = parse_imports("import pathlib")
        assert (
            str(pi.ImportedNames.compare(old, new))
            == "New imported package ``pathlib'' (previously, only ``Path'' was imported from ``pathlib'')"
        )

    def test_general_to_from(self):
        old = parse_imports("import pathlib")
        new = parse_imports("from pathlib import Path")
        assert (
            str(pi.ImportedNames.compare(old, new))
            == "New imported ``Path'' from ``pathlib'' (previously, full ``pathlib'' was imported)"
        )


class TestImportExtractor:
    def test_import_simple(self):
        names = parse_imports("import os")
        assert len(names) == 1
        assert "os" in names

    def test_import_multiple(self):
        names = parse_imports("import os, sys")
        assert len(names) == 2
        assert "os" in names
        assert "sys" in names

    def test_import_alias(self):
        names = parse_imports("import os as operating_system, sys")
        assert len(names) == 2
        assert "operating_system" in names
        assert "sys" in names

    def test_importfrom_simple(self):
        names = parse_imports("from os import path")
        assert len(names) == 1
        assert "path" in names

    def test_importfrom_multiple(self):
        names = parse_imports("from os import path, environ")
        assert len(names) == 2
        assert "path" in names
        assert "environ" in names

    def test_importfrom_alias(self):
        names = parse_imports("from os import path, environ as environment")
        assert len(names) == 2
        assert "path" in names
        assert "environment" in names
