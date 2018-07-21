"""This module containst code that handles comparing function implementations"""

import logging
import pathlib
from typing import Optional, Tuple, FrozenSet, Set

import pyff.modules as pm
import pyff.packages as pp


LOGGER = logging.getLogger(__name__)


class DirectoryPyfference:  # pylint: disable=too-few-public-methods
    """Represents differences between two directories"""

    def __init__(
        self, packages: Optional[pp.PackagesPyfference], modules: Optional[pm.ModulesPyfference]
    ) -> None:
        self.packages: Optional[pp.PackagesPyfference] = packages
        self.modules: Optional[pm.ModulesPyfference] = modules

    def __str__(self):
        output = []
        if self.packages:
            output.append(str(self.packages))
        if self.modules:
            output.append(str(self.modules))

        return "\n".join(output)

    def __bool__(self):
        return bool(self.packages or self.modules)


def find_those_pythonz(
    directory: pathlib.Path
) -> Tuple[FrozenSet[pathlib.Path], FrozenSet[pathlib.Path]]:
    """Find Python packages and modules in a given directory"""
    traverse_directories: Set[pathlib.Path] = {directory}
    packages: Set[pathlib.Path] = set()
    modules: Set[pathlib.Path] = set()
    while traverse_directories:
        candidate = traverse_directories.pop()
        LOGGER.debug("Checking directory for Python content: %s", candidate)
        possible_init = candidate / "__init__.py"
        if possible_init.exists():
            LOGGER.debug("Directory %s is a Python package", candidate)
            packages.add(candidate.relative_to(directory))
            # We do not want to dig into packages
            continue

        for item in candidate.iterdir():
            if item.is_file() and item.suffix == ".py":
                LOGGER.debug("File %s is a Python module", item)
                modules.add(item.relative_to(directory))
            elif item.is_dir():
                LOGGER.debug("Scheduling directory '%s' for traversal", item)
                traverse_directories.add(item)
            else:
                LOGGER.debug("Item %s is not anything Python-related, so we do not care", str(item))

    return (frozenset(packages), frozenset(modules))


def _compare_packages_in_dir(
    old_dir: pathlib.Path,
    new_dir: pathlib.Path,
    old: FrozenSet[pathlib.Path],
    new: FrozenSet[pathlib.Path],
) -> Optional[pp.PackagesPyfference]:
    LOGGER.debug("Packages in the old directory: %s", str(old))
    LOGGER.debug("Packages in the new directory: %s", str(new))

    removed_packages = old - new
    both_packages = old.intersection(new)
    new_packages = new - old

    LOGGER.debug("Removed packages: %s", str(removed_packages))
    LOGGER.debug("Packages in both directories: %s", str(both_packages))
    LOGGER.debug("New packages: %s", str(new_packages))

    removed_package_summaries = {
        pkg: pp.summarize_package(old_dir / pkg) for pkg in removed_packages
    }
    changed_packages = {
        pkg: change
        for pkg, change in [
            (
                pkg,
                pp.pyff_package(
                    pp.summarize_package(old_dir / pkg), pp.summarize_package(new_dir / pkg)
                ),
            )
            for pkg in both_packages
        ]
        if change is not None
    }
    new_package_summaries = {pkg: pp.summarize_package(new_dir / pkg) for pkg in new_packages}

    if removed_package_summaries or changed_packages or new_package_summaries:
        return pp.PackagesPyfference(
            removed_package_summaries, changed_packages, new_package_summaries
        )

    return None


def _compare_modules_in_dir(
    old_dir: pathlib.Path,
    new_dir: pathlib.Path,
    old: FrozenSet[pathlib.Path],
    new: FrozenSet[pathlib.Path],
) -> Optional[pm.ModulesPyfference]:
    LOGGER.debug("Modules in the old directory: %s", str(old))
    LOGGER.debug("Modules in the new directory: %s", str(new))

    removed_modules = old - new
    both_modules = old.intersection(new)
    new_modules = new - old

    LOGGER.debug("Removed modules: %s", str(removed_modules))
    LOGGER.debug("Modules in both directories: %s", str(both_modules))
    LOGGER.debug("New modules: %s", str(new_modules))

    removed_module_summaries = {mod: pm.summarize_module(old_dir / mod) for mod in removed_modules}
    changed_modules = {
        mod: change
        for mod, change in [
            (
                mod,
                pm.pyff_module(
                    pm.summarize_module(old_dir / mod), pm.summarize_module(new_dir / mod)
                ),
            )
            for mod in both_modules
        ]
        if change is not None
    }
    new_module_summaries = {mod: pm.summarize_module(new_dir / mod) for mod in new_modules}

    if removed_module_summaries or changed_modules or new_module_summaries:
        return pm.ModulesPyfference(removed_module_summaries, changed_modules, new_module_summaries)

    return None


def pyff_directory(old: pathlib.Path, new: pathlib.Path) -> Optional[DirectoryPyfference]:
    """Find Python packages and modules in two directories and compare them"""
    if not (old.is_dir() and new.is_dir()):
        raise ValueError(f"At least one of {old}, {new} is not an existing directory")

    old_pkgs, old_mods = find_those_pythonz(old)
    new_pkgs, new_mods = find_those_pythonz(new)

    packages: Optional[pp.PackagesPyfference] = _compare_packages_in_dir(
        old, new, old_pkgs, new_pkgs
    )
    modules: Optional[pm.ModulesPyfference] = _compare_modules_in_dir(old, new, old_mods, new_mods)

    if packages or modules:
        return DirectoryPyfference(packages=packages, modules=modules)

    return None
