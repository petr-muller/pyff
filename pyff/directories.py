"""This module containst code that handles comparing function implementations"""

import logging
import pathlib
from typing import Optional, Tuple, FrozenSet, Set

import pyff.packages as pp


LOGGER = logging.getLogger(__name__)


class DirectoryPyfference:  # pylint: disable=too-few-public-methods
    """Represents differences between two directories"""

    def __init__(self, packages: Optional[pp.PackagesPyfference]) -> None:
        self.packages: Optional[pp.PackagesPyfference] = packages

    def __str__(self):
        output = []
        if self.packages:
            output.append(str(self.packages))

        return "\n".join(output)

    def __bool__(self):
        return bool(self.packages)


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


def pyff_directory(old: pathlib.Path, new: pathlib.Path) -> Optional[DirectoryPyfference]:
    """Find Python packages and modules in two directories and compare them"""
    if not (old.is_dir() and new.is_dir()):
        raise ValueError(f"At least one of {old}, {new} is not an existing directory")

    old_pkgs, old_modules = find_those_pythonz(old)
    new_pkgs, new_modules = find_those_pythonz(new)

    LOGGER.debug("Packages in the old directory: %s", str(old_pkgs))
    LOGGER.debug("Packages in the new directory: %s", str(new_pkgs))
    LOGGER.debug("Modules in the old directory: %s", str(old_modules))
    LOGGER.debug("Modules in the new directory: %s", str(new_modules))

    removed_packages = old_pkgs - new_pkgs
    both_packages = old_pkgs.intersection(new_pkgs)
    new_packages = new_pkgs - old_pkgs

    LOGGER.debug("Removed packages: %s", str(removed_packages))
    LOGGER.debug("Packages in both directories: %s", str(both_packages))
    LOGGER.debug("New packages: %s", str(new_packages))

    removed_package_summaries = {pkg: pp.summarize_package(old / pkg) for pkg in removed_packages}
    changed_packages = {
        pkg: change
        for pkg, change in [
            (pkg, pp.pyff_package(pp.summarize_package(old / pkg), pp.summarize_package(new / pkg)))
            for pkg in both_packages
        ]
        if change is not None
    }
    new_package_summaries = {pkg: pp.summarize_package(new / pkg) for pkg in new_packages}

    if removed_package_summaries or changed_packages or new_package_summaries:
        return DirectoryPyfference(
            packages=pp.PackagesPyfference(
                removed_package_summaries, changed_packages, new_package_summaries
            )
        )

    return None
