"""This module contains code that handles comparing function implementations"""

import ast
import logging
from itertools import zip_longest
from typing import Optional, cast, Set, Dict, List
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

    def __str__(self) -> str:
        lines: List[str] = []
        if self.old_name is not None:
            lines.append(f"Function {hl(self.old_name)} renamed to {hl(self.name)}")

        if self.implementation:
            lines.append(f"Function {hl(self.name)} changed implementation:")

        implementation_changes = []
        for change in self.implementation:
            implementation_changes.append("  - " + change.make_message().replace("\n", "\n  - "))
        lines.extend(sorted(implementation_changes))

        return "\n".join(lines)

    def simplify(self) -> Optional["FunctionPyfference"]:
        """Cleans empty differences, empty sets etc. after manipulation"""
        return self if self.old_name or self.implementation else None

    def __repr__(self):
        return (
            f"FunctionPyfference(name={self.name}, implementation={self.implementation}, "
            f"old_name={self.old_name})"
        )


class FunctionSummary:  # pylint: disable=too-few-public-methods
    """Contains summary information about a function"""

    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash((self.name,))

    def __str__(self):
        return f"function {hl(self.name)}"


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
    old: ast.FunctionDef,
    new: ast.FunctionDef,
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

    for old_statement, new_statement in zip_longest(old.body, new.body):
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
    external_name_usage_difference = compare_import_usage(old, new, old_imports, new_imports)
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

    old_ast = ast.parse(old).body
    new_ast = ast.parse(new).body

    if len(old_ast) != 1 or not isinstance(old_ast[0], ast.FunctionDef):
        raise ValueError(f"First argument does not seem to be a single Python function: {old}")
    if len(new_ast) != 1 or not isinstance(new_ast[0], ast.FunctionDef):
        raise ValueError(f"Second argument does not seem to be a single Python function: {new}")

    return pyff_function(
        cast(ast.FunctionDef, old_ast[0]),
        cast(ast.FunctionDef, new_ast[0]),
        old_imports,
        new_imports,
    )


class FunctionsExtractor(ast.NodeVisitor):
    """Extract information about functions in a module"""

    def __init__(self) -> None:
        self.names: Set[str] = set()
        self.functions: Dict[str, ast.FunctionDef] = {}

    def visit_ClassDef(self, node):  # pylint: disable=invalid-name
        """Prevent this visitor from inspecting classes"""
        pass

    def visit_FunctionDef(self, node):  # pylint: disable=invalid-name
        """Save top-level function definitions"""
        self.names.add(node.name)
        self.functions[node.name] = node


class FunctionsPyfference:  # pylint: disable=too-few-public-methods
    """Holds differences between top-level functions in a module"""

    def __init__(self, new: Set[FunctionSummary], changed: Dict[str, FunctionPyfference]) -> None:
        self.changed: Dict[str, FunctionPyfference] = changed
        self.new: Set[FunctionSummary] = new

    def __str__(self) -> str:
        changed = "\n".join([str(change) for change in self.changed.values()])
        new = "\n".join([f"New {f}" for f in sorted([str(name) for name in self.new])])

        return "\n".join([changeset for changeset in (new, changed) if changeset])

    def simplify(self) -> Optional["FunctionsPyfference"]:
        """Cleans empty differences, empty sets etc. after manipulation"""
        new_changed = {}
        for function, change in self.changed.items():
            new_change = change.simplify()
            if new_change:
                new_changed[function] = new_change
        self.changed = new_changed

        return self if self.new or self.changed else None


def pyff_functions(old: ast.Module, new: ast.Module) -> Optional[FunctionsPyfference]:
    """Return differences in top-level functions in two modules"""
    old_walker = FunctionsExtractor()
    new_walker = FunctionsExtractor()

    old_import_walker = pi.ImportExtractor()
    new_import_walker = pi.ImportExtractor()

    old_walker.visit(old)
    new_walker.visit(new)
    old_import_walker.visit(old)
    new_import_walker.visit(new)

    both = old_walker.names.intersection(new_walker.names)
    LOGGER.debug(f"Functions present in both modules: {both}")
    differences = {}
    for function in both:
        LOGGER.debug(f"Comparing function '{function}'")
        difference = pyff_function(
            old_walker.functions[function],
            new_walker.functions[function],
            old_import_walker.names,
            new_import_walker.names,
        )
        LOGGER.debug(repr(difference))
        if difference:
            LOGGER.debug(f"Function {function} differs")
            differences[function] = difference
        else:
            LOGGER.debug(f"Function {function} is identical")

    new_names = new_walker.names - old_walker.names
    new_functions = {FunctionSummary(name) for name in new_names}
    LOGGER.debug(f"New functions: {new_names}")

    if differences or new_functions:
        LOGGER.debug("Functions differ")
        return FunctionsPyfference(changed=differences, new=new_functions)

    LOGGER.debug("Functions are identical")
    return None
