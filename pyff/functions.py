"""This module contains code that handles comparing function implementations"""

import ast
import logging
from itertools import zip_longest
from typing import Optional, Set, Dict, List, Union, FrozenSet
from collections.abc import Hashable

import pyff.imports as pi
import pyff.statements as ps
from pyff.kitchensink import hl, hlistify


LOGGER = logging.getLogger(__name__)


class FunctionImplementationChange(Hashable):  # pylint: disable=too-few-public-methods
    """Represents any single change in function implementation"""

    def make_message(self) -> str:  # pylint: disable=no-self-use
        """Returns a human-readable message explaining the change"""
        return f"Code semantics changed"

    def __eq__(self, other):
        return isinstance(other, FunctionImplementationChange)

    def __hash__(self):
        return hash("FunctionImplementationChange")

    def __repr__(self):
        return "FunctionImplementationChange"


class ExternalUsageChange(FunctionImplementationChange):  # pylint: disable=too-few-public-methods
    """Represents any change in how function uses external names"""

    def __init__(self, gone: Set[str], appeared: Set[str]) -> None:
        self.gone: Set[str] = gone
        self.appeared: Set[str] = appeared

    def make_message(self) -> str:
        """Returns a human-readable message explaining the change"""
        lines: List[str] = []
        if self.gone:
            lines.append(f"No longer uses imported {hlistify(sorted(self.gone))}")
        if self.appeared:
            lines.append(f"Newly uses imported {hlistify(sorted(self.appeared))}")

        return "\n".join(lines)

    def __eq__(self, other):
        return self.gone == other.gone and self.appeared == other.appeared

    def __hash__(self):
        return hash("ExternalUsageChange")

    def __repr__(self):
        return f"ExternalUsageChange(gone={self.gone}, appeared={self.appeared})"


class StatementChange(FunctionImplementationChange):  # pylint: disable=too-few-public-methods
    """Represents a change between two statements"""

    def __init__(self, change: ps.StatementPyfference) -> None:
        self.change: ps.StatementPyfference = change

    def make_message(self) -> str:
        return str(self.change)

    def __hash__(self):
        return hash("StatementChange")

    def __repr__(self):
        return f"StatementChange(change={self.change})"


class FunctionPyfference:  # pylint: disable=too-few-public-methods
    """Holds differences between Python function definitions"""

    def __init__(
        self,
        name: str,
        implementation: Set[FunctionImplementationChange],
        old_name: Optional[str] = None,
    ) -> None:
        self.name: str = name
        self.old_name: Optional[str] = old_name
        self.implementation: Set[FunctionImplementationChange] = implementation
        self._noun: str = "Function"

    def __str__(self) -> str:
        lines: List[str] = []
        if self.old_name is not None:
            lines.append(f"{self._noun} {hl(self.old_name)} renamed to {hl(self.name)}")

        if self.implementation:
            lines.append(f"{self._noun} {hl(self.name)} changed implementation:")

        implementation_changes = []
        for change in self.implementation:
            implementation_changes.append("  " + change.make_message().replace("\n", "\n  "))
        lines.extend(sorted(implementation_changes))

        return "\n".join(lines)

    def set_method(self):
        """Used when FunctionPyfference is used in context of a class"""
        self._noun = "Method"

    def simplify(self) -> Optional["FunctionPyfference"]:
        """Cleans empty differences, empty sets etc. after manipulation"""
        return self if self.old_name or self.implementation else None

    def __repr__(self):
        return (
            f"FunctionPyfference(name={self.name}, implementation={self.implementation}, "
            f"old_name={self.old_name}, noun={self._noun})"
        )


class FunctionSummary:  # pylint: disable=too-few-public-methods
    """Contains summary information about a function"""

    def __init__(self, name: str, node: ast.FunctionDef, is_property: bool = False) -> None:
        self.node: ast.FunctionDef = node
        self.name: str = name
        self.property: bool = is_property
        self._noun: str = "function"

    def __eq__(self, other):
        return self.name == other.name

    def set_method(self):
        """Used when FunctionPyfference is used in context of a class"""
        self._noun = "method"

    def __str__(self):
        prop = "property " if self.property else ""
        return f"{prop}{self._noun} {hl(self.name)}"

    def __repr__(self):
        return (
            f"FunctionSummary(name={self.name}, node={repr(self.node)}, property={self.property})"
        )


class FunctionPyfferenceRecorder:
    """Records various changes detected in function definitions."""

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.old_name: Optional[str] = None
        self.implementation: Set[FunctionImplementationChange] = set()

    def name_changed(self, old_name: str) -> None:
        """Record a name change of the function."""
        self.old_name = old_name

    def implementation_changed(self, change: FunctionImplementationChange) -> None:
        """Record changes in implementation of the function."""
        self.implementation.add(change)

    def build(self) -> Optional[FunctionPyfference]:
        """Produces final FunctionPyfference from recorded changes.

        If no changes were recorded, return None."""
        if self.old_name is None and not self.implementation:
            return None

        return FunctionPyfference(
            name=self.name, old_name=self.old_name, implementation=self.implementation
        )


class ExternalNamesExtractor(ast.NodeVisitor):
    """Collects information about imported name usage in function"""

    def __init__(self, imported_names: pi.ImportedNames) -> None:
        self.imported_names: pi.ImportedNames = imported_names
        self.names: Set[str] = set()
        self.in_progress: Optional[str] = None

    def visit_Name(self, node):  # pylint: disable=invalid-name
        """Compare all names against a list of imported names"""
        self.in_progress = None
        self.generic_visit(node)
        if node.id in self.imported_names:
            self.names.add(node.id)
        else:
            self.in_progress = node.id

    def visit_Attribute(self, node):  # pylint: disable=invalid-name
        """..."""
        self.in_progress = None
        self.generic_visit(node)
        if self.in_progress is not None:
            self.in_progress = ".".join((self.in_progress, node.attr))
            if self.in_progress in self.imported_names:
                self.names.add(self.in_progress)
                self.in_progress = None


def compare_import_usage(  # pylint: disable=invalid-name
    old: ast.FunctionDef,
    new: ast.FunctionDef,
    old_imports: pi.ImportedNames,
    new_imports: pi.ImportedNames,
) -> Optional[ExternalUsageChange]:
    """Compares external (imported) names usage in two versions of a function.

    Args:
        old: Old version of the function
        new: New version of the function
        old_imports: Imported names available for old version of the function
        new_imports: Imported names available for new version of the function

    Returns:
        ExternalUsageChange object, which is basically a pair of two sets: `appeared`, which
        contains names only used in new version of the function, and `gone`, which contains
        names only used in the old version. If both sets would be empty, None is returned."""

    first_walker = ExternalNamesExtractor(old_imports)
    second_walker = ExternalNamesExtractor(new_imports)

    for statement in old.body:
        first_walker.visit(statement)

    for statement in new.body:
        second_walker.visit(statement)

    appeared = second_walker.names - first_walker.names
    gone = first_walker.names - second_walker.names

    LOGGER.debug(f"Imported names used in old function: {first_walker.names}")
    LOGGER.debug(f"Imported names used in new function: {second_walker.names}")
    LOGGER.debug(f"Imported names not used anymore:     {gone}")
    LOGGER.debug(f"Imported names newly used:           {appeared}")

    if appeared or gone:
        return ExternalUsageChange(gone=gone, appeared=appeared)

    return None


def pyff_function(
    old: FunctionSummary,
    new: FunctionSummary,
    old_imports: pi.ImportedNames,
    new_imports: pi.ImportedNames,
) -> Optional[FunctionPyfference]:
    """Return differences between two Python functions.

    Args:
        old: Old version of Python function.
        new: New version of Python function.
        old_imports: Imported names available for old version of the function
        new_imports: Imported names available for new version of the function

    Returns:
        If the functions are identical, returns None. If they differ, a FunctionPyfference
        object is returned, describing the differences."""

    difference_recorder = FunctionPyfferenceRecorder(new.name)

    if old.name != new.name:
        LOGGER.debug(f"Name differs: old={old.name} new={new.name}")
        difference_recorder.name_changed(old.name)

    for old_statement, new_statement in zip_longest(old.node.body, new.node.body):
        if old_statement is None or new_statement is None:
            LOGGER.debug(f"  old={repr(old_statement)}")
            LOGGER.debug(f"  new={repr(new_statement)}")
            LOGGER.debug(
                "  One statement is None: one function is longer, so implementation changed"
            )
            difference_recorder.implementation_changed(FunctionImplementationChange())
            break

        change = ps.pyff_statement(old_statement, new_statement, old_imports, new_imports)
        if change:
            LOGGER.debug("  Statements are different")
            LOGGER.debug(f"  old={ast.dump(old_statement)}")
            LOGGER.debug(f"  new={ast.dump(new_statement)}")
            LOGGER.debug(f"  change={repr(change)}")
            if change.is_specific():
                difference_recorder.implementation_changed(StatementChange(change))
            else:
                difference_recorder.implementation_changed(FunctionImplementationChange())

    LOGGER.debug("Comparing imported name usage")
    external_name_usage_difference = compare_import_usage(
        old.node, new.node, old_imports, new_imports
    )
    if external_name_usage_difference:
        LOGGER.debug("Imported name usage differs")
        difference_recorder.implementation_changed(external_name_usage_difference)

    return difference_recorder.build()


def pyff_function_code(
    old: str, new: str, old_imports: pi.ImportedNames, new_imports: pi.ImportedNames
) -> Optional[FunctionPyfference]:
    """Return differences between two Python functions.

    Args:
        old: Old version of Python function.
        new: New version of Python function.
        old_imports: Imported names available for old version of the function
        new_imports: Imported names available for new version of the function

    Returns:
        If the functions are identical, returns None. If they differ, a FunctionPyfference
        object is returned, describing the differences."""

    extractor = FunctionsExtractor()
    try:
        extractor.visit(ast.parse(old))
        old_summary = extractor.functions.popitem()[1]
    except KeyError:
        raise ValueError("Old module does not seem to contain exactly one function code")

    try:
        extractor.visit(ast.parse(new))
        new_summary = extractor.functions.popitem()[1]
    except KeyError:
        raise ValueError("Old module does not seem to contain exactly one function code")

    return pyff_function(old_summary, new_summary, old_imports, new_imports)


class FunctionsExtractor(ast.NodeVisitor):
    """Extract information about functions in a module"""

    def __init__(self) -> None:
        self.functions: Dict[str, FunctionSummary] = {}

    def visit_ClassDef(self, node):  # pylint: disable=invalid-name
        """Prevent this visitor from inspecting classes"""
        pass

    @property
    def names(self) -> FrozenSet[str]:
        """Returns a set of names of discovered functions"""
        return frozenset(self.functions.keys())

    @staticmethod
    def _is_property_decorator(node: Union[ast.Name, ast.Attribute]) -> bool:
        return isinstance(node, ast.Name) and node.id == "property"

    def visit_FunctionDef(self, node):  # pylint: disable=invalid-name
        """Save top-level function definitions"""
        is_property: bool = False

        for decorator in node.decorator_list:
            if self._is_property_decorator(decorator):
                is_property = True
                break

        self.functions[node.name] = FunctionSummary(
            name=node.name, node=node, is_property=is_property
        )


class FunctionsPyfference:  # pylint: disable=too-few-public-methods
    """Holds differences between top-level functions in a module"""

    def __init__(
        self,
        new: Dict[str, FunctionSummary],
        changed: Dict[str, FunctionPyfference],
        removed: Dict[str, FunctionSummary],
    ) -> None:
        self.changed: Dict[str, FunctionPyfference] = changed
        self.new: Dict[str, FunctionSummary] = new
        self.removed: Dict[str, FunctionSummary] = removed

    def __str__(self) -> str:
        removed = "\n".join(
            [f"Removed {f}" for f in sorted([str(self.removed[name]) for name in self.removed])]
        )
        changed = "\n".join([str(self.changed[name]) for name in sorted(self.changed)])
        new = "\n".join([f"New {f}" for f in sorted([str(self.new[name]) for name in self.new])])

        return "\n".join([changeset for changeset in (removed, changed, new) if changeset])

    def set_method(self):
        """Used when FunctionPyfference is used in context of a class"""
        for function in self.removed.values():
            function.set_method()
        for function in self.changed.values():
            function.set_method()
        for function in self.new.values():
            function.set_method()

    def simplify(self) -> Optional["FunctionsPyfference"]:
        """Cleans empty differences, empty sets etc. after manipulation"""
        new_changed = {}
        for function, change in self.changed.items():
            new_change = change.simplify()
            if new_change:
                new_changed[function] = new_change
        self.changed = new_changed

        return self if self.new or self.changed or self.removed else None


def pyff_functions(
    old: Union[ast.Module, ast.ClassDef],
    new: Union[ast.Module, ast.ClassDef],
    old_imports: pi.ImportedNames,
    new_imports: pi.ImportedNames,
) -> Optional[FunctionsPyfference]:
    """Return differences in top-level functions in two modules"""
    old_walker = FunctionsExtractor()
    new_walker = FunctionsExtractor()

    for node in old.body:
        old_walker.visit(node)

    for node in new.body:
        new_walker.visit(node)

    both: FrozenSet[str] = old_walker.names.intersection(new_walker.names)
    LOGGER.debug(f"Functions present in both modules: {both}")
    differences: Dict[str, FunctionPyfference] = {}
    for function in both:
        LOGGER.debug(f"Comparing function '{function}'")
        difference = pyff_function(
            old_walker.functions[function], new_walker.functions[function], old_imports, new_imports
        )
        LOGGER.debug(f"Difference: {repr(difference)}")
        if difference:
            LOGGER.debug(f"Function {function} differs")
            differences[function] = difference
        else:
            LOGGER.debug(f"Function {function} is identical")

    new_names: FrozenSet[str] = new_walker.names - old_walker.names
    new_functions: Dict[str, FunctionSummary] = {
        name: new_walker.functions[name] for name in new_names
    }
    LOGGER.debug(f"New functions: {new_names}")

    removed_names: FrozenSet[str] = old_walker.names - new_walker.names
    removed_functions: Dict[str, FunctionSummary] = {
        name: old_walker.functions[name] for name in removed_names
    }
    LOGGER.debug(f"Removed functions: {removed_names}")

    if differences or new_functions or removed_functions:
        LOGGER.debug("Functions differ")
        return FunctionsPyfference(
            removed=removed_functions, changed=differences, new=new_functions
        )

    LOGGER.debug("Functions are identical")
    return None
