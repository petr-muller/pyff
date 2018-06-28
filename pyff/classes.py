"""This module contains code that handles comparing function implementations"""

import ast
import logging
from types import MappingProxyType
from typing import Union, List, Optional, Set, FrozenSet, Dict, Mapping
from pyff.kitchensink import hl, pluralize
import pyff.imports as pi
import pyff.functions as pf


LOGGER = logging.getLogger(__name__)


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
        methods: int,
        private: int,
        definition: ast.ClassDef,
        baseclasses: Optional[List[BaseClassType]] = None,
    ) -> None:
        self.methods: int = methods
        self.private_methods: int = private
        self.public_methods: int = methods - private
        self.baseclasses: Optional[List[BaseClassType]] = baseclasses
        self.definition = definition

    @property
    def name(self):
        """Returns class name"""
        return self.definition.name

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
        self._classes: Dict[str, ClassSummary] = {}
        self._private_methods: int = 0
        self._methods: int = 0
        self._names: Optional[pi.ImportedNames] = names

    @property
    def classes(self) -> Mapping[str, ClassSummary]:
        """Return a set of extracted class summaries"""
        return MappingProxyType(self._classes)

    @property
    def classnames(self) -> FrozenSet[str]:
        """Return a set of class names in the module"""
        return frozenset(self._classes.keys())

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

        summary = ClassSummary(
            self._methods, self._private_methods, baseclasses=bases, definition=node
        )
        self._classes[node.name] = summary

    def visit_FunctionDef(self, node):  # pylint: disable=invalid-name
        """Save counts of encountered private/public methods"""
        if node.name.startswith("_"):
            self._private_methods += 1
        self._methods += 1


class ClassPyfference:  # pylint: disable=too-few-public-methods
    """Represents differences between two classes"""

    def __init__(self, methods: Optional[pf.FunctionsPyfference]) -> None:
        self.methods: Optional[pf.FunctionsPyfference] = methods
        self.name = "Game"

    def __str__(self):
        lines = [f"Class {hl(self.name)} changed:"]
        if self.methods:
            self.methods.set_method()
            methods = str(self.methods)
            lines.append(methods)

        return "\n".join(lines).replace("\n", "\n  ")


class ClassesPyfference:  # pylint: disable=too-few-public-methods
    """Holds differences between classes defined in a module"""

    def __init__(self, new: Set[ClassSummary], changed: Dict[str, ClassPyfference]) -> None:
        self.new: Set[ClassSummary] = new
        self.changed: Dict[str, ClassPyfference] = changed

    def __str__(self):
        new = [f"New {cls}" for cls in sorted(self.new)]
        changed = [str(self.changed[name]) for name in sorted(self.changed)]
        return "\n".join(changed + new)

    def simplify(self) -> Optional["ClassesPyfference"]:
        """Cleans empty differences, empty sets etc. after manipulation"""
        return self if self.new else None


def pyff_class(
    old: ClassSummary,
    new: ClassSummary,
    old_imports: pi.ImportedNames,
    new_imports: pi.ImportedNames,
) -> Optional[ClassPyfference]:
    """Return differences in two classes"""
    methods = pf.pyff_functions(old.definition, new.definition, old_imports, new_imports)
    if methods:
        LOGGER.debug(f"Class '{new.name}' differs")
        return ClassPyfference(methods=methods)

    LOGGER.debug(f"Class '{old.name}' is identical")
    return None


def pyff_classes(
    old: ast.Module, new: ast.Module, old_imports: pi.ImportedNames, new_imports: pi.ImportedNames
) -> Optional[ClassesPyfference]:
    """Return differences in classes defined in two modules"""
    first_walker = ClassesExtractor(names=old_imports)
    second_walker = ClassesExtractor(names=new_imports)

    first_walker.visit(old)
    second_walker.visit(new)

    differences: Dict[str, ClassPyfference] = {}
    both = first_walker.classnames.intersection(second_walker.classnames)
    LOGGER.debug(f"Classes present in both module versions: {both}")
    for klass in both:
        LOGGER.debug(f"Comparing class '{klass}'")
        difference = pyff_class(
            first_walker.classes[klass], second_walker.classes[klass], old_imports, new_imports
        )
        LOGGER.debug(f"Difference: {difference}")
        if difference:
            LOGGER.debug(f"Class {klass} differs")
            differences[klass] = difference
        else:
            LOGGER.debug(f"Class {klass} is identical")

    new_classes = {
        cls for cls in second_walker.classes.values() if cls.name not in first_walker.classnames
    }
    LOGGER.debug(f"New classes: {new_classes}")

    if differences or new_classes:
        LOGGER.debug("Classes differ")
        return ClassesPyfference(new=new_classes, changed=differences)

    LOGGER.debug("Classes are identical")
    return None
