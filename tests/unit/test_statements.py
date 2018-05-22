# pylint: disable=missing-docstring

import ast

import pyff.statements as ps
import pyff.imports as pi

from helpers import parse_imports

# == FullyQualifyNames

def _check_fqn(imports, code, expected_subs, expected_qualified_code):
    imports = parse_imports(imports)
    qualifier = ps.FullyQualifyNames(imports)
    original_ast = ast.parse(code)
    qualified_ast = qualifier.visit(original_ast)
    assert qualifier.substitutions == expected_subs
    assert ast.dump(ast.parse(expected_qualified_code)) == ast.dump(qualified_ast)

def test_FullyQualifyNames_import(): # pylint: disable=invalid-name
    _check_fqn("import os.path as pathy", "pathy.join([1, 2, 3])", {"pathy": "os.path"},
               'os.path.join([1, 2, 3])')
    _check_fqn("import os.path as pathy", "path = pathy", {"pathy": "os.path"},
               "path = os.path")
    _check_fqn("import os.path as pathy", "path = path.pathy", {}, "path = path.pathy")

def test_FullyQualifyNames_importfrom(): # pylint: disable=invalid-name
    _check_fqn("from os import path", "path.join([1, 2, 3])", {"path": "os.path"},
               "os.path.join([1, 2, 3])")
    _check_fqn("from os.path import join", "path = join([1, 2, 3])", {"join": "os.path.join"},
               "path = os.path.join([1, 2, 3])")
    _check_fqn("from one.two.three import four as f", "four = f", {"f": "one.two.three.four"},
               "four = one.two.three.four")
    _check_fqn("from one.two.three import four as f", "three = four", {}, "three = four")

def test_FullyQualifyNames_nosub(): # pylint: disable=invalid-name
    _check_fqn("import os", "os.path.join([1,2,3])", {}, "os.path.join([1,2,3])")

# == SingleExternalNameUsageChange

def test_SingleExternalNameUsageChange_sanity(): # pylint: disable=invalid-name
    change = ps.SingleExternalNameUsageChange(old="os.path", new="pathy")
    assert change.old == "os.path"
    assert change.new == "pathy"

def test_SingleExternalNameUsageChange_equality(): # pylint: disable=invalid-name
    change = ps.SingleExternalNameUsageChange(old="os.path", new="pathy")
    equal = ps.SingleExternalNameUsageChange(old="os.path", new="pathy")
    different = ps.SingleExternalNameUsageChange(old="pathy", new="os.pathy")

    assert change == equal
    assert {change} == {equal}
    assert change != different

# == ImportedReferences

def test_FIPImportedReferences_sanity(): # pylint: disable=invalid-name
    change_1 = ps.SingleExternalNameUsageChange("old", "new")
    change_2 = ps.SingleExternalNameUsageChange("another_old", "just_old")
    fip = ps.ExternalNameUsageChange({change_1, change_2})
    assert len(fip.changes) == 2
    assert ps.SingleExternalNameUsageChange("old", "new") in fip.changes
    assert ps.SingleExternalNameUsageChange("another_old", "just_old") in fip.changes

# == find_external_name_matches

def test_find_external_name_matches_import(): # pylint: disable=invalid-name
    package_imports = parse_imports("import os")
    alias_imports = parse_imports("import os as operatingsystem")

    parse_pkg = lambda: ast.parse("def function(): return os.path.join([1, 2, 3])")
    parse_alias = lambda: ast.parse("def function(): return operatingsystem.path.join([1, 2, 3])")

    assert ps.find_external_name_matches(parse_pkg(), parse_pkg(),
                                         package_imports, package_imports) is None

    changes = ps.find_external_name_matches(parse_pkg(), parse_alias(),
                                            package_imports, alias_imports)
    assert changes is not None
    assert len(changes.changes) == 1
    change = changes.changes.pop()
    assert change.old == 'os'
    assert change.new == 'operatingsystem'

def _check_matches(changeset, length, old, new):
    assert changeset is not None
    assert len(changeset.changes) == length
    change = changeset.changes.pop()
    assert change.old == old
    assert change.new == new

def test_find_external_name_matches_importfrom(): # pylint: disable=invalid-name
    # package_import = parse_imports("import os.path")
    from_import = parse_imports("from os import path")
    alias_import = parse_imports("from os import path as pathy")

    # parse_pkg = lambda: ast.parse("def f(): return os.path.join([1,2,3])")
    parse_from = lambda: ast.parse("def f(): return path.join([1,2,3])")
    parse_alias = lambda: ast.parse("def f(): return pathy.join([1,2,3])")

    # BUG: We do not detect this
    #package_to_from = ps.find_external_name_matches(parse_pkg(), parse_from(),
    #                                                package_import, from_import)
    #_check_matches(package_to_from, 1, "os.path", "path")

    # BUG: We do not detect this
    # package_to_alias = ps.find_external_name_matches(parse_pkg(), parse_alias(),
    #                                                 package_import, alias_import)
    #_check_matches(package_to_alias, 1, "os.path", "pathy")

    from_to_alias = ps.find_external_name_matches(parse_from(), parse_alias(),
                                                  from_import, alias_import)
    _check_matches(from_to_alias, 1, "path", "pathy")

# == StatementPyfference
def test_StatementPyfference_sem_relevant(): # pylint: disable=invalid-name
    pyfference = ps.StatementPyfference()
    assert pyfference.semantically_different()
    pyfference.add_semantically_relevant_change("change")
    assert pyfference.semantically_different()
    assert pyfference.semantically_relevant == {"change"}

def test_StatementPyfference_sem_irrelevant(): # pylint: disable=invalid-name
    pyfference = ps.StatementPyfference()
    assert pyfference.semantically_different()
    pyfference.add_semantically_irrelevant_change("change")
    assert not pyfference.semantically_different()
    assert pyfference.semantically_irrelevant == {"change"}

# == pyff_statement

def test_pyff_statement_identical():
    assert ps.pyff_statement(ast.parse("a = a + b"), ast.parse("a = a + b"), pi.ImportedNames(),
                             pi.ImportedNames()) is None

def test_pyff_statement_different():
    change = ps.pyff_statement(ast.parse("a = a + b"), ast.parse("a = a - b"), pi.ImportedNames(),
                               pi.ImportedNames())
    assert change.semantically_different()

def test_pyff_statements_external_names(): # pylint: disable=invalid-name
    change = ps.pyff_statement(ast.parse("p = path.join(lst)"), ast.parse("p = pathy.join(lst)"),
                               pi.ImportedNames(), pi.ImportedNames())
    # alone, the statements are different
    assert change.semantically_different()

    another_change = ps.pyff_statement(ast.parse("p = path.join(lst)"),
                                       ast.parse("p = pathy.join(lst)"),
                                       parse_imports("from os import path"),
                                       parse_imports("from os import path as pathy"))
    # with information about imports, we can deduce the statements are semantically equivalent
    assert not another_change.semantically_different()
