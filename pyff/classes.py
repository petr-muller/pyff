"""This module contains code that handles comparing function implementations"""

import ast
import logging
from types import MappingProxyType
from typing import Union, List, Optional, Set, FrozenSet, Dict, Mapping
from pyff.kitchensink import hl, pluralize, hlistify
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
        methods: Set[str],
        definition: ast.ClassDef,
        attributes: Set[str],
        baseclasses: Optional[List[BaseClassType]] = None,
    ) -> None:
        self.methods: Set[str] = methods
        self.attributes = frozenset(attributes)
        self.baseclasses: Optional[List[BaseClassType]] = baseclasses
        self.definition = definition

    @property
    def name(self) -> str:
        """Returns class name"""
        return self.definition.name

    @property
    def public_methods(self) -> FrozenSet[str]:
        """Return public methods of the class"""
        return frozenset({method for method in self.methods if not method.startswith("_")})

    @property
    def private_methods(self) -> FrozenSet[str]:
        """Return public methods of the class"""
        return frozenset({method for method in self.methods if method.startswith("_")})

    def __str__(self) -> str:
        LOGGER.debug("String: %s", repr(self))
        class_part: str = f"class {hl(self.name)}"
        methods = pluralize("method", self.public_methods)
        method_part: str = f"with {len(self.public_methods)} public {methods}"

        if not self.baseclasses:
            return f"{class_part} {method_part}"
        elif len(self.baseclasses) == 1:
            return f"{class_part} derived from {str(self.baseclasses[0])} {method_part}"

        raise Exception("Multiple inheritance not yet implemented")

    def __repr__(self):
        return (
            f"ClassSummary(methods={self.methods}, attributes={self.attributes}, "
            f"bases={self.baseclasses}, AST={self.definition}"
        )


class ClassesExtractor(ast.NodeVisitor):
    """Extracts information about classes in a module"""

    class SelfAttributeExtractor(ast.NodeVisitor):
        """Extracts self attributes references used in the node"""

        def __init__(self):
            self.attributes: Set[str] = set()

        def visit_Attribute(self, node):  # pylint: disable=invalid-name
            """self.attribute -> 'attribute'"""
            if isinstance(node.value, ast.Name) and node.value.id == "self":
                self.attributes.add(node.attr)

    class AssignmentExtractor(ast.NodeVisitor):
        """Extracts self attributes used as assignment targets"""

        def __init__(self):
            self.attributes: Set[str] = set()
            self.extractor = ClassesExtractor.SelfAttributeExtractor()

        def visit_Assign(self, node):  # pylint: disable=invalid-name
            """'self.attribute = value' -> 'attribute'"""
            for target in node.targets:
                self.extractor.visit(target)
            self.attributes.update(self.extractor.attributes)

        def visit_AnnAssign(self, node):  # pylint: disable=invalid-name
            """'self.attribute: typehint = value' -> 'attribute'"""
            self.extractor.visit(node.target)
            self.attributes.update(self.extractor.attributes)

    class MethodExtractor(ast.NodeVisitor):
        """Extracts information about a method"""

        @staticmethod
        def extract_attributes(node: ast.FunctionDef) -> FrozenSet[str]:
            """Extract attributes used in the method"""
            LOGGER.debug("Extracting attributes from method '%s", node.name)
            extractor = ClassesExtractor.AssignmentExtractor()
            for statement in node.body:
                extractor.visit(statement)

            LOGGER.debug("Discovered attributes '%s'", extractor.attributes)
            return frozenset(extractor.attributes)

        def __init__(self):
            self.methods: Set[str] = set()
            self.attributes: Set[str] = set()

        def visit_FunctionDef(self, node):  # pylint: disable=invalid-name
            """Save counts of encountered private/public methods"""
            LOGGER.debug("Extracting information about method '%s'", node.name)
            self.methods.add(node.name)
            self.attributes.update(self.extract_attributes(node))

    def __init__(self, names: Optional[pi.ImportedNames] = None) -> None:
        self._classes: Dict[str, ClassSummary] = {}
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
        LOGGER.debug("Extracting information about class '%s'", node.name)

        extractor = ClassesExtractor.MethodExtractor()
        extractor.visit(node)

        bases: List[str] = []
        for base in node.bases:
            if base.id in self._names:
                LOGGER.debug("Imported ancestor class '%s', base.id")
                bases.append(ImportedBaseClass(base.id))
            else:
                LOGGER.debug("Local ancestor class '%s', base.id")
                bases.append(LocalBaseClass(base.id))

        summary = ClassSummary(
            extractor.methods, baseclasses=bases, definition=node, attributes=extractor.attributes
        )
        self._classes[node.name] = summary


class AttributesPyfference:  # pylint: disable=too-few-public-methods
    """Represents differnces between attributes of two classes"""

    def __init__(self, removed: FrozenSet[str], new: FrozenSet[str]) -> None:
        self.removed: FrozenSet[str] = removed
        self.new: FrozenSet[str] = new

    def __str__(self):
        lines: List[str] = []
        if self.removed:
            lines.append(
                f"Removed {pluralize('attribute', self.removed)} {hlistify(sorted(self.removed))}"
            )
        if self.new:
            lines.append(f"New {pluralize('attribute', self.new)} {hlistify(sorted(self.new))}")

        return "\n".join(lines)

    def __bool__(self) -> bool:
        return bool(self.removed or self.new)


class ClassPyfference:  # pylint: disable=too-few-public-methods
    """Represents differences between two classes"""

    def __init__(
        self,
        name: str,
        attributes: Optional[AttributesPyfference],
        methods: Optional[pf.FunctionsPyfference],
    ) -> None:
        self.attributes: Optional[AttributesPyfference] = attributes
        self.methods: Optional[pf.FunctionsPyfference] = methods
        self.name = name

    def __str__(self):
        lines = [f"Class {hl(self.name)} changed:"]
        if self.attributes:
            lines.append(str(self.attributes))
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
    attributes = AttributesPyfference(
        removed=old.attributes - new.attributes, new=new.attributes - old.attributes
    )
    if methods or attributes:
        LOGGER.debug(f"Class '{new.name}' differs")
        return ClassPyfference(name=new.name, methods=methods, attributes=attributes)

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
