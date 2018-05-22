"""This module contains code that handles comparing imports"""

from collections.abc import Mapping
from typing import Set, Dict, Union, Optional
import ast
from pyff.kitchensink import hl, hlistify, pluralize

ImportNode = Union[ast.Import, ast.ImportFrom]  # pylint: disable=invalid-name


class ImportedName:  # pylint: disable=too-few-public-methods
    """Represents a single imported name"""

    def __init__(self, name: str, node: ImportNode, alias: ast.alias) -> None:
        self.name: str = name
        self.node: ImportNode = node
        self.alias: ast.alias = alias

    def __repr__(self):  # pragma: no cover
        return f"ImportedName(name={self.name} node={self.node} alias={self.alias}"

    @property
    def canonical_name(self):
        """Returns whole name.

        Example: For 'join' imported by 'from os.path import join', returns 'os.path.join'"""
        if isinstance(self.node, ast.Import):
            return self.alias.name
        elif isinstance(self.node, ast.ImportFrom):
            return f"{self.node.module}.{self.alias.name}"

        raise Exception("Node should always be one of {Import, ImportFrom}")  # pragma: no cover

    @property
    def canonical_ast(self):
        """Returns AST node for the full name

        Example: For 'join' imported by 'from os.path import join', returns AST of 'os.path.join'"""
        if isinstance(self.node, ast.Import):
            items = self.alias.name.split(".")
            node = ast.Name(id=items.pop(0), ctx=ast.Load())
            while items:
                node = ast.Attribute(value=node, attr=items.pop(0), ctx=ast.Load())
            return node
        elif isinstance(self.node, ast.ImportFrom):
            items = self.node.module.split(".") + [self.alias.name]
            node = ast.Name(id=items.pop(0), ctx=ast.Load())
            while items:
                node = ast.Attribute(value=node, attr=items.pop(0), ctx=ast.Load())
            return node

        raise Exception("Node should always be one of {Import, ImportFrom}")  # pragma: no cover

    def __str__(self):
        return self.name


class ImportsPyfference:
    """Represent difference between two ImportedNames."""

    def __init__(self):
        self.new_imports: Set[ImportedName] = set()
        self.removed_imports: Set[ImportedName] = set()
        self.new_fromimports: Dict[str, Set[ImportedName]] = {}
        self.removed_fromimports: Dict[str, Set[ImportedName]] = {}
        self.new_fromimport_modules: Set[str] = set()
        self.removed_fromimport_modules: Set[str] = set()

    def __bool__(self):
        return bool(
            (
                self.new_imports
                or self.removed_imports
                or self.new_fromimports
                or self.removed_fromimports
                or self.new_fromimport_modules
                or self.removed_fromimport_modules
            )
        )

    def simplify(self):
        """Cleans empty differences, empty sets etc. after manipulation"""
        return self if self else None

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

        for module, names in self.removed_fromimports.items():
            removed_names = sorted([str(name) for name in names])
            hl_removed_names = hlistify(removed_names)
            if module in self.removed_fromimport_modules:
                lines.append(f"Removed import of {hl_removed_names} from removed {hl(module)}")
            else:
                lines.append(f"Removed import of {hl_removed_names} from {hl(module)}")

        for module, names in self.new_fromimports.items():
            new_names = sorted([str(name) for name in names])
            if module in self.new_fromimport_modules:
                lines.append(f"New imported {hlistify(new_names)} from new {hl(module)}")
            else:
                lines.append(f"New imported {hlistify(new_names)} from {hl(module)}")

        return "\n".join(lines)


class ImportedNames(Mapping):  # pylint: disable=too-few-public-methods
    """Dictionary mapping external names to appropriate ImportedName"""

    @staticmethod
    def compare(old: "ImportedNames", new: "ImportedNames") -> Optional[ImportsPyfference]:
        """Compare two sets of imported names."""
        change = ImportsPyfference()
        for name, node in new.names.items():
            if name not in old.names:
                if isinstance(node.node, ast.Import):
                    change.new_imports.add(node)
                elif isinstance(node.node, ast.ImportFrom) and node.node.module:
                    if node.node.module not in change.new_fromimports:
                        change.new_fromimports[node.node.module] = set()
                    change.new_fromimports[node.node.module].add(node)

        for name, node in old.names.items():
            if name not in new.names:
                if isinstance(node.node, ast.Import):
                    change.removed_imports.add(node)
                elif isinstance(node.node, ast.ImportFrom) and node.node.module:
                    if node.node.module not in change.removed_fromimports:
                        change.removed_fromimports[node.node.module] = set()
                    change.removed_fromimports[node.node.module].add(node)

        change.new_fromimport_modules = new.from_modules - old.from_modules
        change.removed_fromimport_modules = old.from_modules - new.from_modules

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
