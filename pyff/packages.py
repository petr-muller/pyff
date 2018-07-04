"""This module contains code that handles comparing packages"""
import logging
import pathlib
import ast

from typing import Optional, Iterable, FrozenSet, Set
from astroid.modutils import get_module_files

import pyff.modules as pm

LOGGER = logging.getLogger(__name__)


class PackagePyfference:  # pylint: disable=too-few-public-methods
    """Holds differences between two Python packages"""

    def __init__(self, modules: Optional[pm.ModulesPyfference]) -> None:
        self.modules: Optional[pm.ModulesPyfference] = modules

    def __str__(self):
        return str(self.modules)

    def __repr__(self):
        return f"PackagePyfference(modules={repr(self.modules)})"


def extract_modules(files: Iterable[pathlib.Path], package_path: pathlib.Path) -> FrozenSet[str]:
    """Extract direct modules of a packages (i.e. not modules of subpackages"""
    LOGGER.debug(str(files))
    LOGGER.debug(str(package_path))
    return frozenset({module.name for module in files if module.parents[0] == package_path})


def _compare_module_in_packages(
    module: pathlib.Path, old_package: pathlib.Path, new_package: pathlib.Path
) -> Optional[pm.ModulePyfference]:
    """Compare one module in two packages"""
    old_module = old_package / module
    new_module = new_package / module

    return pm.pyff_module_code(old_module.read_text(), new_module.read_text())


def _summarize_module_in_package(module: pathlib.Path, package: pathlib.Path) -> pm.ModuleSummary:
    full_path = package / module
    module_ast = ast.parse(full_path.read_text())
    return pm.ModuleSummary(str(module), module_ast)


def pyff_package(
    old_package: pathlib.Path, new_package: pathlib.Path
) -> Optional[PackagePyfference]:
    """Given *paths* to two versions of a package, return differences between them"""
    old_files: Set[pathlib.Path] = {
        pathlib.Path(module) for module in get_module_files(old_package, ())
    }
    new_files: Set[pathlib.Path] = {
        pathlib.Path(module) for module in get_module_files(new_package, ())
    }

    LOGGER.debug("Files of the old package %s: %s", old_package, old_files)
    LOGGER.debug("Files of the new package %s: %s", new_package, new_files)

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
