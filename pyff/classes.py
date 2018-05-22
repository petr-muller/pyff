"""This module contains code that handles comparing function implementations"""

import ast
from typing import Union, List, Optional, Set, FrozenSet
from pyff.kitchensink import hl, pluralize
import pyff.imports as pi


class LocalBaseClass:
    # pylint: disable=too-few-public-methods
    """Represents part of a class summary for case when base class is local"""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"local {hl(self.name)}"


class ImportedBaseClass:
    # pylint: disable=too-few-public-methods
    """Represents part of a class summary for case when base class is imported"""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"imported {hl(self.name)}"


BaseClassType = Union[LocalBaseClass, ImportedBaseClass]  # pylint: disable=invalid-name


class ClassSummary:  # pylint: disable=too-few-public-methods
    """Contains summary information about a class"""

    def __init__(
        self,
        name: str,
        methods: int,
        private: int,
        baseclasses: Optional[List[BaseClassType]] = None,
    ) -> None:
        self.name: str = name
        self.methods: int = methods
        self.private_methods: int = private
        self.public_methods: int = methods - private
        self.baseclasses: Optional[List[BaseClassType]] = baseclasses

    def __str__(self) -> str:
        class_part: str = f"class {hl(self.name)}"
        methods = pluralize("method", self.public_methods)
        method_part: str = f"with {self.public_methods} public {methods}"

        if not self.baseclasses:
            return f"{class_part} {method_part}"
        elif len(self.baseclasses) == 1:
            return f"{class_part} derived from {str(self.baseclasses[0])} {method_part}"

        raise Exception("Multiple inheritance not yet implemented")


class ClassesExtractor(ast.NodeVisitor):
    """Extracts information about classes in a module"""

    def __init__(self, names: Optional[pi.ImportedNames] = None) -> None:
        self._classes: Set[ClassSummary] = set()
        self._private_methods: int = 0
        self._methods: int = 0
        self._names: Optional[pi.ImportedNames] = names

    @property
    def classes(self) -> FrozenSet[ClassSummary]:
        """Return a set of extracted class summaries"""
        return frozenset(self._classes)

    @property
    def classnames(self) -> Set[str]:
        """Return a set of class names in the module"""
        return {cls.name for cls in self._classes}

    def visit_ClassDef(self, node):  # pylint: disable=invalid-name
        """Save information about classes that appeared in a module"""
        self._private_methods: int = 0
        self._methods: int = 0
        self.generic_visit(node)

        bases: List[str] = []
        for base in node.bases:
            if base.id in self._names:
                bases.append(ImportedBaseClass(base.id))
            else:
                bases.append(LocalBaseClass(base.id))

        summary = ClassSummary(node.name, self._methods, self._private_methods, baseclasses=bases)
        self._classes.add(summary)

    def visit_FunctionDef(self, node):  # pylint: disable=invalid-name
        """Save counts of encountered private/public methods"""
        if node.name.startswith("_"):
            self._private_methods += 1
        self._methods += 1


class ClassesPyfference:  # pylint: disable=too-few-public-methods
    """Holds differences between classes defined in a module"""

    def __init__(self, new: Set[ClassSummary]) -> None:
        self.new: Set[ClassSummary] = new

    def __str__(self):
        return "\n".join([f"New {cls}" for cls in sorted(self.new)])

    def simplify(self) -> Optional["ClassesPyfference"]:
        """Cleans empty differences, empty sets etc. after manipulation"""
        return self if self.new else None


def pyff_classes(old: ast.Module, new: ast.Module) -> Optional[ClassesPyfference]:
    """Return differences in classes defined in two modules"""
    old_import_walker = pi.ImportExtractor()
    new_import_walker = pi.ImportExtractor()

    old_import_walker.visit(old)
    new_import_walker.visit(new)

    first_walker = ClassesExtractor(names=old_import_walker.names)
    second_walker = ClassesExtractor(names=new_import_walker.names)

    first_walker.visit(old)
    second_walker.visit(new)

    appeared = {cls for cls in second_walker.classes if cls.name not in first_walker.classnames}

    return ClassesPyfference(appeared) if appeared else None
