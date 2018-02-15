"""Classes holding information about differences between individual Python elements"""
from collections import namedtuple
from typing import Tuple, List, Dict, Iterable
from pyff.summary import ClassSummary

Change = namedtuple("Change", ["old", "new"])

class FunctionPyfference:  # pylint: disable=too-few-public-methods
    """Holds differences between Python function definitions"""
    def __init__(self, name: str, names: Tuple[str, str] = None,
                 implementation: bool = None, appeared_import_usage: Iterable[str] = None) -> None:
        self.name = name
        self.names: Change = None
        self.changes: List = []
        self.implementation: bool = implementation
        self.appeared_import_usage: Iterable[str] = appeared_import_usage

        if names:
            self.names = Change(names[0], names[1])
            self.changes.append(self.names)

        if implementation:
            self.changes.append(f"Function '{self.name}' changed implementation")

    def __len__(self):
        return len(self.changes)

    def __str__(self):
        suffix = ""
        if self.appeared_import_usage:
            names = [f"'{name}'" for name in self.appeared_import_usage]
            suffix = ", newly uses external names " + ", ".join(names)

        if self.names and self.implementation:
            old = self.names.old
            new = self.names.new
            return f"Function '{old}' renamed to '{new}' and its implementation changed" + suffix
        elif self.names:
            return f"Function '{self.names.old}' renamed to '{self.names.new}'"
        elif self.implementation:
            return f"Function '{self.name}' changed implementation" + suffix

        return ""

class FromImportPyfference: # pylint: disable=too-few-public-methods
    """Holds differences between from X import Y statements in a module"""
    def __init__(self, new: Dict[str, List[str]]) -> None:
        self.new = new

    def __str__(self):
        template = "Added import of new names {names} from new package '{package}'"
        lines = []
        for package, values in self.new.items():
            names = ", ".join([f"'{name}'" for name in values])
            lines.append(template.format(names=names, package=package))

        return "\n".join(lines)

class FunctionsPyfference: # pylint: disable=too-few-public-methods
    """Holds differences between top-level functions in a module"""
    def __init__(self, changed: Dict[str, FunctionPyfference]) -> None:
        self.changed = changed

    def __str__(self) -> str:

        return "\n".join([str(change) for change in self.changed.values()])

class ClassesPyfference: # pylint: disable=too-few-public-methods

    """Holds differences between classes defined in a module"""
    def __init__(self, new: Iterable[ClassSummary]) -> None:
        self.new: Iterable[ClassSummary] = new

    def __str__(self):
        return "\n".join([f"New {cls}" for cls in self.new])

class ModulePyfference:  # pylint: disable=too-few-public-methods
    """Holds differences between two Python modules"""
    def __init__(self, from_imports: FromImportPyfference = None,
                 classes: ClassesPyfference = None,
                 functions: FunctionsPyfference = None) -> None:
        self.changes: List = []
        self.from_imports: FromImportPyfference = None
        self.classes: ClassesPyfference = None
        self.functions: FunctionsPyfference = None

        if from_imports:
            self.from_imports = from_imports
            self.changes.append(self.from_imports)

        if classes:
            self.classes = classes
            self.changes.append(self.classes)

        if functions:
            self.functions = functions
            self.changes.append(self.functions)

    def __len__(self):
        return len(self.changes)

    def __str__(self):
        return "\n".join([str(change) for change in self.changes])
