"""This module contains code that handles comparing statements"""

import ast
import logging
import copy
from typing import Set, Optional, Dict
import pyff.imports as pi
from pyff.kitchensink import hl


LOGGER = logging.getLogger(__name__)


class SingleExternalNameUsageChange:
    """Represents a single external name usage change in a statement."""

    # pylint: disable=too-few-public-methods

    def __init__(self, old: str, new: str) -> None:
        self.old: str = old
        self.new: str = new

        self._key = (old, new)

    def __eq__(self, other):
        return (
            isinstance(other, SingleExternalNameUsageChange)
            and self.old == other.old
            and self.new == other.new
        )

    def __hash__(self):
        return hash(self._key)

    def __repr__(self):  # pragma: no cover
        return f"SingleExternalNameUsageChange(old={self.old}, new={self.new})"

    def __str__(self):
        return f"References of {hl(self.old)} were changed to {hl(self.new)}"


class ExternalNameUsageChange:
    """Represents case where two statements differ only in how they use external names.

    Example:
        (1) something = os.path.join(...)
        (2) something = path.join(...)

        Provided statement (1) runs in context where 'import os.path' was
        executed and (2) runs in context where 'from os import path' was imported,
        the two statements are semantically identical."""

    # pylint: disable=too-few-public-methods

    def __init__(self, changes: Set[SingleExternalNameUsageChange]) -> None:
        self.changes: Set[SingleExternalNameUsageChange] = changes

    def __repr__(self):  # pragma: no cover
        return f"ExternalNameUsageChange(changes={self.changes})"

    def __str__(self):
        return "\n".join(sorted([str(line) for line in self.changes]))


class FullyQualifyNames(ast.NodeTransformer):
    """Transform a statement to a one where external names are fully qualified.

    Example:
        Given a statement 'a = join(...)' and an information that join() was
        imported by 'from os.path import join' statement, produce
        'a = os.path.join(...)' statement. The visitor also records which
        substitutions were made.
    """

    def __init__(self, imports: pi.ImportedNames) -> None:
        super(FullyQualifyNames, self).__init__()
        self.external_names: pi.ImportedNames = imports
        self.substitutions: Dict[str, str] = {}
        self.references: Dict[str, str] = {}
        self._current = None

    def visit_Name(self, node):  # pylint: disable=invalid-name, missing-docstring
        self._current = None
        if node.id in self.external_names:
            self._current = self.external_names[node.id].canonical_name
            self.references[self._current] = node.id
            if node.id == self._current:
                return node

            self.substitutions[node.id] = self._current
            return self.external_names[node.id].canonical_ast

        return node

    def visit_Attribute(self, node):  # pylint: disable=invalid-name, missing-docstring
        self.generic_visit(node)
        if self._current:
            prefix = self._current
            self._current = ".".join([prefix, node.attr])
            key = self.references[prefix]
            self.references[self._current] = ".".join([key, node.attr])

        return node


def find_external_name_matches(
    old: ast.AST, new: ast.AST, old_imports: pi.ImportedNames, new_imports: pi.ImportedNames
) -> Optional[ExternalNameUsageChange]:
    """Tests two statements for semantical equality w.r.t. external name usage.

    Example:
        (1) something = os.path.join(...)
        (2) something = path.join(...)

        Provided statement (1) runs in context where 'import os.path' was
        executed and (2) runs in context where 'from os import path' was imported,
        the two statements are semantically identical.

    Args:
        old: AST of the old version of the statement
        new: AST of the new version of the statement
        old_imports: Imported names available for old version of the enclosing functions
        new_imports: Imported names available for new version of the enclosing functions

    Returns:
        If the statements are identical, returns None. If the statements differ
        in something else than external name usage, returns None. Otherwise,
        returns a set of ExternalInStmtChange objects, each
        representing a single external name usage change."""

    if ast.dump(old) == ast.dump(new):
        return None

    fq_old_transformer = FullyQualifyNames(old_imports)
    fq_new_transformer = FullyQualifyNames(new_imports)

    LOGGER.debug("Fully qualifying old statement")
    fq_old = fq_old_transformer.visit(copy.deepcopy(old))
    LOGGER.debug("Fully qualifying new statement")
    fq_new = fq_new_transformer.visit(copy.deepcopy(new))

    changes: Set[SingleExternalNameUsageChange] = set()

    if ast.dump(fq_old) == ast.dump(fq_new):
        LOGGER.debug("Statements are identical after full qualification")
        LOGGER.debug(f"Old statement references: {fq_old_transformer.references}")
        LOGGER.debug(f"New statement references: {fq_new_transformer.references}")
        for original, fqdn in fq_old_transformer.substitutions.items():
            LOGGER.debug(f"'{original}' was fully qualified as '{fqdn}' in old statement")
            if fqdn in fq_new_transformer.references:
                changes.add(
                    SingleExternalNameUsageChange(original, fq_new_transformer.references[fqdn])
                )

        for original, fqdn in fq_new_transformer.substitutions.items():
            LOGGER.debug(f"'{original}' was fully qualified as '{fqdn}' in new statement")
            if fqdn in fq_old_transformer.references:
                changes.add(
                    SingleExternalNameUsageChange(fq_old_transformer.references[fqdn], original)
                )

    return ExternalNameUsageChange(changes) if changes else None


class StatementPyfference:
    """Describes differences between two statements."""

    def __init__(self) -> None:
        # These functions are intentionally not typed
        self.semantically_relevant: Set = set()
        self.semantically_irrelevant: Set = set()

    def add_semantically_irrelevant_change(self, change) -> None:  # pylint: disable=invalid-name
        """Adds semantically irrelevant change."""
        self.semantically_irrelevant.add(change)

    def add_semantically_relevant_change(self, change) -> None:  # pylint: disable=invalid-name
        """Adds semantically relevant change."""
        self.semantically_relevant.add(change)

    def semantically_different(self) -> bool:
        """Returns whether the differences make the statements semantically different.

        Returns:
            If all known changes are semantically irrelevant, return False.
            Otherwise, return True. If there are no known changes, assume the statements
            were semantically different."""
        # Either we know we have some semantically relevant change,
        # or we have NO IDENTIFIED change, therefore we must assume
        # the difference is semantically relevant
        return bool(self.semantically_relevant or not self.semantically_irrelevant)

    def __str__(self):
        lines = []
        for change in self.semantically_relevant:
            lines.append(str(change))

        for change in self.semantically_irrelevant:
            lines.append(str(change))

        return "\n".join(lines)

    def __repr__(self):
        return (
            f"StatementPyfference(relevant={repr(self.semantically_relevant)}, "
            f"irrelevant={repr(self.semantically_irrelevant)})"
        )

    def is_specific(self) -> bool:
        """Returns True if we have at least one identified code change."""
        return bool(self.semantically_relevant or self.semantically_irrelevant)


def pyff_statement(
    old_statement: ast.AST,
    new_statement: ast.AST,
    old_imports: pi.ImportedNames,
    new_imports: pi.ImportedNames,
) -> Optional[StatementPyfference]:
    """Compare two statements.

    Args:
        old_statement: Old version of the statement
        new_statement: New version of the statement
        old_imports: Imported names available for old version of the statement
        new_imports: Imported names available for new version of the statement

    Returns:
        If the statements are identical, returns None. If they differ, a StatementPyfference
        object, describing the differences is returned."""

    if ast.dump(old_statement) == ast.dump(new_statement):
        return None

    pyfference = StatementPyfference()

    change = find_external_name_matches(old_statement, new_statement, old_imports, new_imports)
    if change:
        LOGGER.debug("Statements are semantically identical but differ in imported name references")
        pyfference.add_semantically_irrelevant_change(change)

    return pyfference
