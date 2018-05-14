"""Reductions are difference post-processing operations"""

from typing import List
from pyff.kitchensink import hl
from pyff.pyfference import ModulePyfference

class ImportReduce:
    """Detects changes from 'from X import Y' to 'import X'"""
    # pylint: disable=too-few-public-methods

    class FromImportToImport:
        """Represents a change from 'from X import Y' to 'import X'"""
        # pylint: disable=too-few-public-methods
        def __init__(self, package: str, names: List[str]) -> None:
            self.package: str = package
            self.old_names: List[str] = names

        def __str__(self):
            old_names = ", ".join([f"{hl(name)}" for name in sorted(self.old_names)])
            tense = "was" if len(self.old_names) == 1 else "were"
            return f'New imported package {hl(self.package)} (previously, only {old_names} {tense} imported from {hl(self.package)})' # pylint: disable=line-too-long

    @staticmethod
    def _merge_fimport_to_import(pyfference, name):
        old_names = pyfference.from_imports.removed[name]
        del pyfference.from_imports.removed[name]
        pyfference.imports.new.remove(name)

        change = ImportReduce.FromImportToImport(name, old_names)
        pyfference.other.append(change)

    @staticmethod
    def apply(pyfference: ModulePyfference) -> None:
        """Reduce changes from 'from X import Y' to 'import X'

        In a given ModulePyfference, detect matching differences where `from X import Y` statements
        were removed and `import X` were added. Remove these differences and add a new difference
        that represents the change as a whole"""
        if not (pyfference.imports and pyfference.from_imports):
            return

        for name in set(pyfference.imports.new):
            if name in pyfference.from_imports.removed:
                ImportReduce._merge_fimport_to_import(pyfference, name)

        pyfference.simplify()
