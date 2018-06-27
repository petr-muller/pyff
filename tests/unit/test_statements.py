# pylint: disable=missing-docstring, no-self-use, too-few-public-methods

import ast

import pyff.statements as ps
import pyff.imports as pi

from helpers import parse_imports


class TestFullyQualifyNames:
    @staticmethod
    def _check_fqn(imports, code, expected_subs, expected_qualified_code):
        imports = parse_imports(imports)
        qualifier = ps.FullyQualifyNames(imports)
        original_ast = ast.parse(code)
        qualified_ast = qualifier.visit(original_ast)
        assert qualifier.substitutions == expected_subs
        assert ast.dump(ast.parse(expected_qualified_code)) == ast.dump(qualified_ast)

    @staticmethod
    def _check_references(imports, code, references):
        imports = parse_imports(imports)
        qualifier = ps.FullyQualifyNames(imports)
        qualifier.visit(ast.parse(code))
        assert qualifier.references == references

    def test_import(self):
        self._check_fqn(
            "import os.path as pathy",
            "pathy.join([1, 2, 3])",
            {"pathy": "os.path"},
            "os.path.join([1, 2, 3])",
        )
        self._check_fqn(
            "import os.path as pathy", "path = pathy", {"pathy": "os.path"}, "path = os.path"
        )
        self._check_fqn("import os.path as pathy", "path = path.pathy", {}, "path = path.pathy")

    def test_importfrom(self):
        self._check_fqn(
            "from os import path",
            "path.join([1, 2, 3])",
            {"path": "os.path"},
            "os.path.join([1, 2, 3])",
        )
        self._check_fqn(
            "from os.path import join",
            "path = join([1, 2, 3])",
            {"join": "os.path.join"},
            "path = os.path.join([1, 2, 3])",
        )
        self._check_fqn(
            "from one.two.three import four as f",
            "four = f",
            {"f": "one.two.three.four"},
            "four = one.two.three.four",
        )
        self._check_fqn("from one.two.three import four as f", "three = four", {}, "three = four")

    def test_nosub(self):
        self._check_fqn("import os", "os.path.join([1,2,3])", {}, "os.path.join([1,2,3])")

    def test_references(self):
        self._check_references(
            "import os",
            "os.path.join([1,2,3])",
            {"os": "os", "os.path": "os.path", "os.path.join": "os.path.join"},
        )

    def test_references_from(self):
        self._check_references(
            "from os import path",
            "path.join([1,2,3])",
            {"os.path": "path", "os.path.join": "path.join"},
        )

    def test_references_alias(self):
        self._check_references(
            "from os import path as pathy",
            "pathy.join([1,2,3])",
            {"os.path": "pathy", "os.path.join": "pathy.join"},
        )


class TestSingleExternalNameUsageChange:
    def test_sanity(self):
        change = ps.SingleExternalNameUsageChange(old="os.path", new="pathy")
        assert change.old == "os.path"
        assert change.new == "pathy"
        assert str(change) == "References of ``os.path'' were changed to ``pathy''"

    def test_equality(self):
        change = ps.SingleExternalNameUsageChange(old="os.path", new="pathy")
        equal = ps.SingleExternalNameUsageChange(old="os.path", new="pathy")
        different = ps.SingleExternalNameUsageChange(old="pathy", new="os.pathy")

        assert change == equal
        assert {change} == {equal}
        assert change != different


class TestExternalNameUsageChange:
    def test_sanity(self):
        change_1 = ps.SingleExternalNameUsageChange("old", "new")
        change_2 = ps.SingleExternalNameUsageChange("another_old", "just_old")
        fip = ps.ExternalNameUsageChange({change_1, change_2})
        assert len(fip.changes) == 2
        assert ps.SingleExternalNameUsageChange("old", "new") in fip.changes
        assert ps.SingleExternalNameUsageChange("another_old", "just_old") in fip.changes
        assert str(fip) == "\n".join(sorted([str(change_1), str(change_2)]))


class TestFindExternalNameMatches:
    @staticmethod
    def _check_matches(changeset, length, old, new):
        assert changeset is not None
        assert len(changeset.changes) == length
        change = changeset.changes.pop()
        assert change.old == old
        assert change.new == new

    def test_import(self):
        package_imports = parse_imports("import os")
        alias_imports = parse_imports("import os as operatingsystem")

        parse_pkg = lambda: ast.parse("def function(): return os.path.join([1, 2, 3])")
        parse_alias = lambda: ast.parse(
            "def function(): return operatingsystem.path.join([1, 2, 3])"
        )

        assert (
            ps.find_external_name_matches(
                parse_pkg(), parse_pkg(), package_imports, package_imports
            )
            is None
        )

        changes = ps.find_external_name_matches(
            parse_pkg(), parse_alias(), package_imports, alias_imports
        )
        assert changes is not None
        assert len(changes.changes) == 1
        change = changes.changes.pop()
        assert change.old == "os"
        assert change.new == "operatingsystem"

    def test_importfrom(self):
        # package_import = parse_imports("import os.path")
        from_import = parse_imports("from os import path")
        alias_import = parse_imports("from os import path as pathy")

        # parse_pkg = lambda: ast.parse("def f(): return os.path.join([1,2,3])")
        parse_from = lambda: ast.parse("def f(): return path.join([1,2,3])")
        parse_alias = lambda: ast.parse("def f(): return pathy.join([1,2,3])")

        # BUG: We do not detect this
        # package_to_from = ps.find_external_name_matches(parse_pkg(), parse_from(),
        #                                                package_import, from_import)
        # _check_matches(package_to_from, 1, "os.path", "path")

        # BUG: We do not detect this
        # package_to_alias = ps.find_external_name_matches(parse_pkg(), parse_alias(),
        #                                                 package_import, alias_import)
        # _check_matches(package_to_alias, 1, "os.path", "pathy")

        from_to_alias = ps.find_external_name_matches(
            parse_from(), parse_alias(), from_import, alias_import
        )
        self._check_matches(from_to_alias, 1, "path", "pathy")

    def test_example_04(self):
        old_import = parse_imports("from pathlib import Path")
        new_import = parse_imports("import pathlib")

        old = ast.parse("Path.home()")
        new = ast.parse("pathlib.Path.home()")

        change = ps.find_external_name_matches(old, new, old_import, new_import)
        assert change is not None


class TestStatementPyfference:
    def test_sem_relevant(self):
        pyfference = ps.StatementPyfference()
        assert pyfference.semantically_different()
        pyfference.add_semantically_relevant_change("change")
        assert pyfference.semantically_different()
        assert pyfference.semantically_relevant == {"change"}
        assert str(pyfference) == "change"

    def test_sem_irrelevant(self):
        pyfference = ps.StatementPyfference()
        assert pyfference.semantically_different()
        pyfference.add_semantically_irrelevant_change("change")
        assert not pyfference.semantically_different()
        assert pyfference.semantically_irrelevant == {"change"}
        assert str(pyfference) == "change"


class TestPyffStatement:
    def test_identical(self):
        assert (
            ps.pyff_statement(
                ast.parse("a = a + b"),
                ast.parse("a = a + b"),
                pi.ImportedNames(),
                pi.ImportedNames(),
            )
            is None
        )

    def test_different(self):
        change = ps.pyff_statement(
            ast.parse("a = a + b"), ast.parse("a = a - b"), pi.ImportedNames(), pi.ImportedNames()
        )
        assert change.semantically_different()

    def test_external_names(self):
        change = ps.pyff_statement(
            ast.parse("p = path.join(lst)"),
            ast.parse("p = pathy.join(lst)"),
            pi.ImportedNames(),
            pi.ImportedNames(),
        )
        # alone, the statements are different
        assert change.semantically_different()

        another_change = ps.pyff_statement(
            ast.parse("p = path.join(lst)"),
            ast.parse("p = pathy.join(lst)"),
            parse_imports("from os import path"),
            parse_imports("from os import path as pathy"),
        )
        # with information about imports, we can deduce the statements are semantically equivalent
        assert not another_change.semantically_different()
