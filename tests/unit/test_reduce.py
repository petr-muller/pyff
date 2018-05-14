# pylint: disable=missing-docstring

import pyff.pyfference as pf
import pyff.reduce as pr

def test_from_import_import():
    from_imports = pf.FromImportPyfference(removed={'os': ['path']}, new={})
    imports = pf.ImportPyfference(new={'os'}, removed=set())
    pyfference = pf.ModulePyfference(from_imports=from_imports, imports=imports)
    pr.ImportReduce.apply(pyfference)

    assert not pyfference.from_imports
    assert not pyfference.imports
    assert str(pyfference) == "New imported package ``os'' (previously, only ``path'' was imported from ``os'')" # pylint: disable=line-too-long

def test_from_import_import_remain():
    from_imports = pf.FromImportPyfference(removed={'os': ['path'], 'sys': ['exit']}, new={})
    imports = pf.ImportPyfference(new={'os', 'argparse'}, removed=set())
    pyfference = pf.ModulePyfference(from_imports=from_imports, imports=imports)
    pr.ImportReduce.apply(pyfference)

    assert pyfference.from_imports
    assert pyfference.imports
    assert str(pyfference) == """Removed import of names ``exit'' from package ``sys''
New imported packages ``argparse''
New imported package ``os'' (previously, only ``path'' was imported from ``os'')"""

def test_from_import_import_plural():
    from_imports = pf.FromImportPyfference(removed={'os': ['path', 'environ']}, new={})
    imports = pf.ImportPyfference(new={'os'}, removed=set())
    pyfference = pf.ModulePyfference(from_imports=from_imports, imports=imports)
    pr.ImportReduce.apply(pyfference)

    assert not pyfference.from_imports
    assert not pyfference.imports
    assert str(pyfference) == "New imported package ``os'' (previously, only ``environ'', ``path'' were imported from ``os'')" # pylint: disable=line-too-long
