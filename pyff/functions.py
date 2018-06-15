"""This module contains code that handles comparing function implementations"""

import ast
from itertools import zip_longest
from typing import Optional, cast, Set, Dict, List
from collections.abc import Hashable

import pyff.imports as pi
import pyff.statements as ps
from pyff.kitchensink import hl, hlistify


class FunctionImplementationChange(Hashable):  # pylint: disable=too-few-public-methods
    """Represents any single change in function implementation"""

    def make_message(self) -> str:  # pylint: disable=no-self-use
        """Returns a human-readable message explaining the change"""
        return f"Code semantics changed"

    def __eq__(self, other):
        return isinstance(other, FunctionImplementationChange)

    def __hash__(self):
        return hash("FunctionImplementationChange")


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


class StatementChange(FunctionImplementationChange):  # pylint: disable=too-few-public-methods
    """Represents a change between two statements"""

    def __init__(self, change: ps.StatementPyfference) -> None:
        self.change: ps.StatementPyfference = change


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
            implementation_changes.append("  - " + change.make_message().replace("\n", "\n  -"))
        lines.extend(sorted(implementation_changes))

        return "\n".join(lines)

    def simplify(self) -> Optional["FunctionPyfference"]:
        """Cleans empty differences, empty sets etc. after manipulation"""
        return self if self.old_name or self.implementation else None


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


def compare_import_usage(
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

    first_walker.visit(old)
    second_walker.visit(new)

    appeared = second_walker.names - first_walker.names
    gone = first_walker.names - second_walker.names

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
        difference_recorder.name_changed(old.name)

    for old_statement, new_statement in zip_longest(old.body, new.body):
        if old_statement is None or new_statement is None:
            difference_recorder.implementation_changed(FunctionImplementationChange())
            break

        change = ps.pyff_statement(old_statement, new_statement, old_imports, new_imports)
        if change:
            difference_recorder.implementation_changed(StatementChange(change))

    external_name_usage_difference = compare_import_usage(old, new, old_imports, new_imports)
    if external_name_usage_difference:
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
    differences = {}
    for function in both:
        difference = pyff_function(
            old_walker.functions[function],
            new_walker.functions[function],
            old_import_walker.names,
            new_import_walker.names,
        )
        if difference:
            differences[function] = difference

    new_names = new_walker.names - old_walker.names
    new_functions = {FunctionSummary(name) for name in new_names}

    if differences or new_functions:
        return FunctionsPyfference(changed=differences, new=new_functions)

    return None
