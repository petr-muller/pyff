"""Classes holding information about differences between individual Python elements"""
from collections import namedtuple
from typing import Tuple, List, Dict, Iterable
from pyff.summary import ClassSummary

Change = namedtuple("Change", ["old", "new"])

class FunctionPyfference:  # pylint: disable=too-few-public-methods
    """Holds differences between Python function definitions"""
    def __init__(self, names: Tuple[str, str] = None) -> None:
        self.name: Change = None
        self.changes: List[Change] = []

        if names:
            self.name = Change(names[0], names[1])
            self.changes.append(self.name)

    def __len__(self):
        return len(self.changes)

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

class ClassesPyfference: # pylint: disable=too-few-public-methods
    """Holds differences between classes defined in a module"""
    def __init__(self, new: Iterable[ClassSummary]) -> None:
        self.new: Iterable[ClassSummary] = new

    def __str__(self):
        return "\n".join([f"New {cls}" for cls in self.new])

class ModulePyfference:  # pylint: disable=too-few-public-methods
    """Holds differences between two Python modules"""
    def __init__(self, from_imports: FromImportPyfference = None,
                 classes: ClassesPyfference = None) -> None:
        self.changes: List = []
        self.from_imports: FromImportPyfference = None
        self.classes: ClassesPyfference = None

        if from_imports:
            self.from_imports = from_imports
            self.changes.append(self.from_imports)

        if classes:
            self.classes = classes
            self.changes.append(self.classes)

    def __len__(self):
        return len(self.changes)

    def __str__(self):
        return "\n".join([str(change) for change in self.changes])
