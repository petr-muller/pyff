"""This module contains code that handles comparing packages"""
import logging
import pathlib
import ast

from typing import Optional, Iterable, FrozenSet, Set, Dict, Mapping
from types import MappingProxyType
from astroid.modutils import get_module_files

import pyff.modules as pm
from pyff.kitchensink import hl, hlistify, pluralize

LOGGER = logging.getLogger(__name__)


class PackageSummary:  # pylint: disable=too-few-public-methods
    """Holds information about a Python package"""

    def __init__(self, package: pathlib.Path) -> None:
        self.path = package


class PackagePyfference:  # pylint: disable=too-few-public-methods
    """Holds differences between two Python packages"""

    def __init__(self, modules: Optional[pm.ModulesPyfference]) -> None:
        self.modules: Optional[pm.ModulesPyfference] = modules

    def __str__(self):
        return str(self.modules)

    def __repr__(self):
        return f"PackagePyfference(modules={repr(self.modules)})"


class PackagesPyfference:  # pylint: disable=too-few-public-methods
    """Holds differences between packages in package or directory"""

    def __init__(
        self,
        removed: Dict[pathlib.Path, PackageSummary],
        changed: Dict[pathlib.Path, PackagePyfference],
        new: Dict[pathlib.Path, PackageSummary],
    ) -> None:
        self._removed: Dict[pathlib.Path, PackageSummary] = removed
        self._changed: Dict[pathlib.Path, PackagePyfference] = changed
        self._new: Dict[pathlib.Path, PackageSummary] = new

    @property
    def removed(self) -> Mapping[pathlib.Path, PackageSummary]:
        """Read-only view on removed packages"""
        return MappingProxyType(self._removed)

    @property
    def new(self) -> Mapping[pathlib.Path, PackageSummary]:
        """Read-only view on new packages"""
        return MappingProxyType(self._new)

    @property
    def changed(self) -> Mapping[pathlib.Path, PackagePyfference]:
        """Read-only view on changed packages"""
        return MappingProxyType(self._changed)

    def __str__(self):
        lines = []
        if self._removed:
            lines.append(f"Removed {pluralize('package', self._removed)} {hlistify(self._removed)}")

        if self._changed:
            lines.append(
                "\n".join(
                    [
                        f"Package {hl(package)} changed:\n  " + str(change).replace("\n", "\n  ")
                        for package, change in self._changed.items()
                    ]
                )
            )

        if self._new:
            lines.append(f"New {pluralize('package', self._new)} {hlistify(self._new)}")

        return "\n".join(lines)

    def __bool__(self):
        return bool(self._removed or self._changed or self._new)


def extract_modules(files: Iterable[pathlib.Path], package: PackageSummary) -> FrozenSet[str]:
    """Extract direct modules of a packages (i.e. not modules of subpackages"""
    return frozenset({module.name for module in files if module.parents[0] == package.path})


def _compare_module_in_packages(
    module: pathlib.Path, old_package: PackageSummary, new_package: PackageSummary
) -> Optional[pm.ModulePyfference]:
    """Compare one module in two packages"""
    old_module = old_package.path / module
    new_module = new_package.path / module

    return pm.pyff_module_code(old_module.read_text(), new_module.read_text())


def summarize_package(package: pathlib.Path) -> PackageSummary:
    """Create a PackageSummary for a given path"""
    return PackageSummary(package)


def _summarize_module_in_package(module: pathlib.Path, package: PackageSummary) -> pm.ModuleSummary:
    full_path = package.path / module
    module_ast = ast.parse(full_path.read_text())
    return pm.ModuleSummary(str(module), module_ast)


def pyff_package(
    old_package: PackageSummary, new_package: PackageSummary
) -> Optional[PackagePyfference]:
    """Given summaries of two versions of a package, return differences between them"""
    old_files: Set[pathlib.Path] = {
        pathlib.Path(module) for module in get_module_files(old_package.path, ())
    }
    new_files: Set[pathlib.Path] = {
        pathlib.Path(module) for module in get_module_files(new_package.path, ())
    }

    LOGGER.debug("Files of the old package %s: %s", str(old_package.path), old_files)
    LOGGER.debug("Files of the new package %s: %s", str(new_package.path), new_files)

    old_modules: Set[pathlib.Path] = {
        pathlib.Path(module) for module in extract_modules(old_files, old_package)
    }
    new_modules: Set[pathlib.Path] = {
        pathlib.Path(module) for module in extract_modules(new_files, new_package)
    }

    LOGGER.debug("Old modules: %s", str(old_modules))
    LOGGER.debug("New modules: %s", str(new_modules))

    removed = old_modules - new_modules
    new = new_modules - old_modules
    both = old_modules.intersection(new_modules)

    LOGGER.debug("Removed modules: %s", str(removed))
    LOGGER.debug("Modules in both packages: %s", str(both))
    LOGGER.debug("New modules: %s", str(new))

    removed_summaries = {
        str(module): _summarize_module_in_package(module, old_package) for module in removed
    }
    new_summaries = {
        str(module): _summarize_module_in_package(module, new_package) for module in new
    }
    changed = {
        str(module): change
        for module, change in [
            (module, _compare_module_in_packages(module, old_package, new_package))
            for module in both
        ]
        if change is not None
    }
    modules = pm.ModulesPyfference(removed_summaries, changed, new_summaries)

    if modules:
        return PackagePyfference(modules)

    return None


def pyff_package_path(old: pathlib.Path, new: pathlib.Path) -> Optional[PackagePyfference]:
    """Given *paths* to two versions of a package, return differences between them"""
    old_summary = summarize_package(old)
    new_summary = summarize_package(new)
    return pyff_package(old_summary, new_summary)
