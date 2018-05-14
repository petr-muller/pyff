"""Classes holding information about differences between individual Python elements"""

from collections import namedtuple
from typing import Tuple, List, Dict, Iterable, Set, Optional
from pyff.summary import ClassSummary, FunctionSummary
from pyff.kitchensink import hl

Change = namedtuple("Change", ["old", "new"])

class ImportPyfference: # pylint: disable=too-few-public-methods
    """Holds differences between `import X` statements in a module"""
    def __init__(self, new: Set[str], removed: Set[str]) -> None:
        self.new: Set[str] = new
        self.removed: Set[str] = removed

    def __str__(self):
        lines = []
        removed = ", ".join([f"{hl(package)}" for package in sorted(self.removed)])
        if removed:
            lines.append(f"Removed import of packages {removed}")

        new = ", ".join([f"{hl(package)}" for package in sorted(self.new)])
        if new:
            lines.append(f"New imported packages {new}")


        return "\n".join(lines)

class FunctionPyfference:  # pylint: disable=too-few-public-methods
    """Holds differences between Python function definitions"""
    def __init__(self, name: str, names: Tuple[str, str] = None,
                 implementation: bool = None, appeared_import_usage: Iterable[str] = None) -> None:
        self.name = name
        self.names: Optional[Change] = None
        self.changes: List = []
        self.implementation: Optional[bool] = implementation
        self.appeared_import_usage: Optional[Iterable[str]] = appeared_import_usage

        if names:
            self.names = Change(names[0], names[1])
            self.changes.append(self.names)

        if implementation:
            self.changes.append(f"Function {hl(self.name)} changed implementation")

    def __len__(self):
        return len(self.changes)

    def __str__(self):
        suffix = ""
        if self.appeared_import_usage:
            names = [f"{hl(name)}" for name in self.appeared_import_usage]
            suffix = ", newly uses external names " + ", ".join(names)

        if self.names and self.implementation:
            old = f"{hl(self.names.old)}"
            new = f"{hl(self.names.new)}"
            return f"Function {old} renamed to {new} and its implementation changed" + suffix
        elif self.names:
            old = f"{hl(self.names.old)}"
            new = f"{hl(self.names.new)}"
            return f"Function {old} renamed to {new}"
        elif self.implementation:
            return f"Function {hl(self.name)} changed implementation" + suffix

        return ""

class FromImportPyfference: # pylint: disable=too-few-public-methods
    """Holds differences between from X import Y statements in a module"""
    def __init__(self, new: Dict[str, List[str]], removed: Dict[str, List[str]]) -> None:
        self.new: Dict[str, List[str]] = new
        self.removed: Dict[str, List[str]] = removed

    def __str__(self):
        remove_template = "Removed import of names {names} from package {package}"
        lines = []
        for package, values in sorted(self.removed.items()):
            names = ", ".join([f"{hl(name)}" for name in sorted(values)])
            lines.append(remove_template.format(names=names, package=f"{hl(package)}"))

        new_template = "New imported names {names} from new package {package}"
        for package, values in sorted(self.new.items()):
            names = ", ".join([f"{hl(name)}" for name in sorted(values)])
            lines.append(new_template.format(names=names, package=f"{hl(package)}"))

        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self.new) + len(self.removed)

class FunctionsPyfference: # pylint: disable=too-few-public-methods
    """Holds differences between top-level functions in a module"""
    def __init__(self, new: Set[FunctionSummary], changed: Dict[str, FunctionPyfference]) -> None:
        self.changed: Dict[str, FunctionPyfference] = changed
        self.new: Set[FunctionSummary] = new

    def __str__(self) -> str:
        changed = "\n".join([str(change) for change in self.changed.values()])
        new = "\n".join([f"New {f}" for f in sorted([str(name) for name in self.new])])

        return "\n".join([changeset for changeset in (new, changed) if changeset])

    def __len__(self) -> int:
        return len(self.changed) + len(self.new)

class ClassesPyfference: # pylint: disable=too-few-public-methods

    """Holds differences between classes defined in a module"""
    def __init__(self, new: Set[ClassSummary]) -> None:
        self.new: Set[ClassSummary] = new

    def __str__(self):
        return "\n".join([f"New {cls}" for cls in sorted([str(cls) for cls in self.new])])

    def __len__(self) -> int:
        return len(self.new)

class ModulePyfference:  # pylint: disable=too-few-public-methods
    """Holds differences between two Python modules"""
    def __init__(self, from_imports: Optional[FromImportPyfference] = None,
                 imports: Optional[ImportPyfference] = None,
                 classes: Optional[ClassesPyfference] = None,
                 functions: Optional[FunctionsPyfference] = None) -> None:
        self.other: List = []
        self.from_imports: Optional[FromImportPyfference] = None
        self.imports: Optional[ImportPyfference] = None
        self.classes: Optional[ClassesPyfference] = None
        self.functions: Optional[FunctionsPyfference] = None

        if from_imports:
            self.from_imports = from_imports

        if imports:
            self.imports = imports

        if classes:
            self.classes = classes

        if functions:
            self.functions = functions

    def __str__(self):
        changes = [self.from_imports, self.imports, self.classes, self.functions] + self.other
        return "\n".join([str(change) for change in changes if change is not None])

    def simplify(self) -> None:
        """Cleans empty differences, empty sets etc. after manipulation"""
        if self.from_imports is not None and not (self.from_imports.removed or
                                                  self.from_imports.new):
            self.from_imports = None

        if self.imports is not None and not (self.imports.removed or self.imports.new):
            self.imports = None
