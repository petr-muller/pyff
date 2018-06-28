"""This module contains code that handles comparing imports"""

import collections.abc
import types
from typing import Set, Dict, Union, Optional, FrozenSet, Mapping, cast
import ast
import logging
from pyff.kitchensink import hl, hlistify, pluralize

ImportNode = Union[ast.Import, ast.ImportFrom]  # pylint: disable=invalid-name

LOGGER = logging.getLogger(__name__)


class ImportedName:
    """Represents a single imported name"""

    def __init__(self, name: str, node: ImportNode, alias: ast.alias) -> None:
        self.name: str = name
        self.node: ImportNode = node
        self.alias: ast.alias = alias

    def __repr__(self):  # pragma: no cover
        return f"ImportedName(name={self.name} node={self.node} alias={self.alias}"

    def is_import(self) -> bool:
        """Returns True if name was imported with `import X` statement"""
        return isinstance(self.node, ast.Import)

    def is_import_from(self) -> bool:
        """Returns True if name was imported with `from Y import X` statement"""
        return isinstance(self.node, ast.ImportFrom)

    @property
    def canonical_name(self) -> str:
        """Returns whole name.

        Example: For 'join' imported by 'from os.path import join', returns 'os.path.join'"""
        if isinstance(self.node, ast.Import):
            return self.alias.name
        elif isinstance(self.node, ast.ImportFrom):
            return f"{self.node.module}.{self.alias.name}"

        raise Exception("Node should always be one of {Import, ImportFrom}")  # pragma: no cover

    @property
    def canonical_ast(self) -> Union[ast.Name, ast.Attribute]:
        """Returns AST node for the full name

        Example: For 'join' imported by 'from os.path import join', returns AST of 'os.path.join'"""
        node: Union[ast.Name, ast.Attribute]

        if isinstance(self.node, ast.Import):
            items = self.alias.name.split(".")
            node = ast.Name(id=items.pop(0), ctx=ast.Load())
            while items:
                node = ast.Attribute(value=node, attr=items.pop(0), ctx=ast.Load())
            return node
        elif isinstance(self.node, ast.ImportFrom):
            if self.node.module is None:
                raise Exception(
                    "ast.ImportFrom has module attribute set to None"
                )  # pragma: no cover
            items = self.node.module.split(".") + [self.alias.name]
            node = ast.Name(id=items.pop(0), ctx=ast.Load())
            while items:
                node = ast.Attribute(value=node, attr=items.pop(0), ctx=ast.Load())
            return node

        raise Exception("Node should always be one of {Import, ImportFrom}")  # pragma: no cover

    def __str__(self):
        return self.name


class FromImportPyfference:
    """Represents difference in `from X import Y` between two ImportedNames"""

    def __init__(self):
        self._new: Dict[str, Set[ImportedName]] = {}
        self._removed: Dict[str, Set[ImportedName]] = {}
        self._new_modules: Set[str] = set()
        self._removed_modules: Set[str] = set()

    @property
    def new(self) -> Mapping[str, Set[ImportedName]]:
        """Returns a read-only mapping of new imported-from names"""
        return types.MappingProxyType(self._new)

    @property
    def removed(self) -> Mapping[str, Set[ImportedName]]:
        """Returns a read-only mapping of removed imported-from names"""
        return types.MappingProxyType(self._removed)

    @property
    def new_modules(self) -> FrozenSet[str]:
        """Returns a read-only set of new modules imported via `from X import Y` statements"""
        return frozenset(self._new_modules)

    @property
    def removed_modules(self) -> FrozenSet[str]:
        """Returns a read-only set of removed modules imported via `from X import Y` statements"""
        return frozenset(self._removed_modules)

    def add_new(self, node: ImportedName) -> None:
        """Add new name imported by `from X import y` statement"""
        if not node.is_import_from():
            raise ValueError(
                "FromImportPyfference can only handle ImportFrom nodes"
            )  # pragma: no cover

        module = cast(ast.ImportFrom, node.node).module

        if module is None:
            raise Exception("ast.ImportFrom has `module` attribute set to None")  # pragma: no cover

        if module not in self._new:
            self._new[module] = set()
        self._new[module].add(node)

    def add_removed(self, node: ImportedName) -> None:
        """Add removed name imported by `from X import y` statement"""
        if not node.is_import_from():
            raise ValueError(
                "FromImportPyfference can only handle ImportFrom nodes"
            )  # pragma: no cover

        module = cast(ast.ImportFrom, node.node).module
        if module is None:
            raise Exception("ast.ImportFrom has `module` attribute set to None")  # pragma: no cover

        if module not in self._removed:
            self._removed[module] = set()
        self._removed[module].add(node)

    def add_new_modules(self, modules: Set[str]) -> None:
        """Add new modules imported via `from X import Y` statements"""
        self._new_modules.update(modules)

    def add_removed_modules(self, modules: Set[str]) -> None:
        """Add removed modules imported via `from X import Y` statements"""
        self._removed_modules.update(modules)

    def delete_new_module(self, module: str) -> None:
        """Delete new module imported via `from X import Y` statements"""
        self._new_modules.discard(module)
        if module in self._new:
            del self._new[module]

    def delete_removed_module(self, module: str) -> None:
        """Delete removed module imported via `from X import Y` statements"""
        self._removed_modules.discard(module)
        if module in self._removed:
            del self._removed[module]

    def __bool__(self):
        return bool(self._new or self.removed or self.new_modules or self.removed_modules)


class ImportsPyfference:
    """Represent difference between two ImportedNames."""

    def __init__(self):
        self._new_imports: Set[ImportedName] = set()
        self._removed_imports: Set[ImportedName] = set()
        self.fromimports: FromImportPyfference = FromImportPyfference()
        self._changed_to_fromimport: Dict[str, Set[ImportedName]] = {}
        self._changed_to_import: Dict[str, Set[ImportedName]] = {}

    def __bool__(self):
        return bool(
            (
                self._new_imports
                or self._removed_imports
                or self.fromimports
                or self._changed_to_fromimport
                or self._changed_to_import
            )
        )

    @property
    def new_imports(self) -> FrozenSet[ImportedName]:
        """Returns a read-only set of new imported names"""
        return frozenset(self._new_imports)

    @property
    def removed_imports(self) -> FrozenSet[ImportedName]:
        """Returns a read-only set of removed imported names"""
        return frozenset(self._removed_imports)

    def simplify(self) -> Optional["ImportsPyfference"]:
        """Cleans empty differences, empty sets etc. after manipulation"""
        return self if self else None

    def new_import(self, node: ImportedName) -> None:
        """Add a new imported name"""
        self._new_imports.add(node)

    def removed_import(self, node: ImportedName) -> None:
        """Add a removed imported name"""
        self._removed_imports.add(node)

    def new_from_import(self, node: ImportedName) -> None:
        """Add a new name imported via `from X import Y` statement"""
        if not node.is_import_from():
            raise ValueError(
                "ImportsPyfference.new_from_import can only handle ImportFrom nodes"
            )  # pragma: no cover

        if cast(ast.ImportFrom, node.node).module:
            self.fromimports.add_new(node)

    def removed_from_import(self, node: ImportedName) -> None:
        """Add a removed name imported via `from X import Y` statement"""
        if not node.is_import_from():
            raise ValueError(
                "ImportsPyfference.new_from_import can only handle ImportFrom nodes"
            )  # pragma: no cover

        if cast(ast.ImportFrom, node.node).module:
            self.fromimports.add_removed(node)

    def new_fromimport_modules(self, modules: Set[str]) -> None:
        """Add new modules imported via `from X import Y` statement"""
        self.fromimports.add_new_modules(modules)

    def removed_fromimport_modules(self, modules: Set[str]) -> None:
        """Add removed modules imported via `from X import Y` statement"""
        self.fromimports.add_removed_modules(modules)

    def reduce(self) -> None:
        """Find special cases and other reductions in the differences

        (1) Find matching names imported by different import statements and
            create special records for these changes.
            Example: `from os import path` in one version and `import os` in another"""
        for name in set(self._new_imports):
            if name.name in self.fromimports.removed_modules:
                LOGGER.debug(
                    f"New module has 'import {name}' "
                    f"and old module had 'from {name} import ...': "
                    f"Adding a change record"
                )
                self._new_imports.discard(name)
                self._changed_to_import[name.name] = self.fromimports.removed[name.name]
                self.fromimports.delete_removed_module(name.name)

        for name in set(self._removed_imports):
            if name.name in self.fromimports.new_modules:
                self._removed_imports.discard(name)
                self._changed_to_fromimport[name.name] = self.fromimports.new[name.name]
                self.fromimports.delete_new_module(name.name)
                LOGGER.debug(
                    f"Old module had 'import {name}' and "
                    f"new module has 'from {name} import ...': "
                    f"Adding a change record"
                )

    def __str__(self):
        lines = []
        removed_imports = sorted([name.name for name in self.removed_imports])
        if removed_imports:
            packages = pluralize("package", removed_imports)
            names = hlistify(removed_imports)
            lines.append(f"Removed import of {packages} {names}")

        new_imports = sorted([name.name for name in self.new_imports])
        if new_imports:
            packages = pluralize("package", new_imports)
            names = hlistify(new_imports)
            lines.append(f"New imported {packages} {names}")

        for module, names in self.fromimports.removed.items():
            removed_names = sorted([str(name) for name in names])
            hl_removed_names = hlistify(removed_names)
            if module in self.fromimports.removed_modules:
                lines.append(f"Removed import of {hl_removed_names} from removed {hl(module)}")
            else:
                lines.append(f"Removed import of {hl_removed_names} from {hl(module)}")

        for module, names in self.fromimports.new.items():
            new_names = sorted([str(name) for name in names])
            if module in self.fromimports.new_modules:
                lines.append(f"New imported {hlistify(new_names)} from new {hl(module)}")
            else:
                lines.append(f"New imported {hlistify(new_names)} from {hl(module)}")

        for module, names in self._changed_to_fromimport.items():
            new_names = sorted([str(name) for name in names])
            lines.append(
                f"New imported {hlistify(new_names)} from {hl(module)} "
                f"(previously, full {hl(module)} was imported)"
            )

        for module, names in self._changed_to_import.items():
            new_names = sorted([str(name) for name in names])
            was = "was" if len(new_names) == 1 else "were"
            lines.append(
                f"New imported package {hl(module)} "
                f"(previously, only {hlistify(new_names)} "
                f"{was} imported from {hl(module)})"
            )

        return "\n".join(lines)


class ImportedNames(collections.abc.Mapping):  # pylint: disable=too-few-public-methods
    """Dictionary mapping external names to appropriate ImportedName"""

    @staticmethod
    def extract(code: ast.Module) -> "ImportedNames":
        """Extracts ImportedNames from a Module"""
        import_walker = ImportExtractor()
        import_walker.visit(code)
        return import_walker.names

    @staticmethod
    def compare(old: "ImportedNames", new: "ImportedNames") -> Optional[ImportsPyfference]:
        """Compare two sets of imported names."""
        LOGGER.debug("Comparing ImportedNames")
        change = ImportsPyfference()
        for name, node in new.names.items():
            if name not in old.names:
                LOGGER.debug(f"New name '{name}' not present in old names")
                if node.is_import():
                    change.new_import(node)
                elif node.is_import_from():
                    change.new_from_import(node)

        for name, node in old.names.items():
            if name not in new.names:
                LOGGER.debug(f"Old name '{name}' not present in new names")
                if node.is_import():
                    change.removed_import(node)
                elif node.is_import_from():
                    change.removed_from_import(node)

        change.new_fromimport_modules(new.from_modules - old.from_modules)
        LOGGER.debug(f"New modules from which names were imported: " f"{change.fromimports.new}")
        change.removed_fromimport_modules(old.from_modules - new.from_modules)
        LOGGER.debug(
            f"Removed modules from which names were imported: " f"{change.fromimports.removed}"
        )

        change.reduce()

        return change if change else None

    def __init__(self) -> None:
        self.names: Dict[str, ImportedName] = {}
        self.from_modules: Set[str] = set()

    def __getitem__(self, item):
        return self.names[item]

    def __iter__(self):
        yield from self.names

    def __len__(self):
        return len(self.names)

    def __repr__(self):  # pragma: no cover
        return f"ImportedNames(names={self.names}, from_modules={self.from_modules}"

    def _add(self, name: ast.alias, node: ImportNode) -> None:
        if name.asname is not None:
            self.names[name.asname] = ImportedName(name.asname, node, alias=name)
        else:
            self.names[name.name] = ImportedName(name.name, node, alias=name)

    def add_import(self, node: ast.Import) -> None:
        """Add a 'import X, Y' statement"""
        for name in node.names:
            self._add(name, node)

    def add_importfrom(self, node: ast.ImportFrom) -> None:
        """Add a 'from X import Y' statement"""
        for name in node.names:
            self._add(name, node)
        if node.module:
            self.from_modules.add(node.module)


class ImportExtractor(ast.NodeVisitor):
    """Extracts information about import and 'import from' statements"""

    def __init__(self) -> None:
        self.names = ImportedNames()
        super(ImportExtractor, self).__init__()

    def visit_Import(self, node):  # pylint: disable=invalid-name
        """Save information about `import X, Y` statements"""
        self.names.add_import(node)

    def visit_ImportFrom(self, node):  # pylint: disable=invalid-name
        """Save information about `from x import y` statements"""
        self.names.add_importfrom(node)


def pyff_imports(old: ast.Module, new: ast.Module) -> Optional[ImportsPyfference]:
    """Return differences in import statements in two modules"""
    old_walker = ImportExtractor()
    new_walker = ImportExtractor()

    old_walker.visit(old)
    new_walker.visit(new)

    difference = ImportedNames.compare(old_walker.names, new_walker.names)

    return difference if difference else None


def pyff_imports_code(old_code: str, new_code: str) -> Optional[ImportsPyfference]:
    """Return differences in import statements in two modules"""
    old_ast = ast.parse(old_code)
    new_ast = ast.parse(new_code)

    return pyff_imports(old_ast, new_ast)
