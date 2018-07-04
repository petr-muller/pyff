"""This module contains code that handles comparing modules"""

import ast
import logging
from typing import List, Optional, Dict

import pyff.classes as pc
import pyff.functions as pf
import pyff.imports as pi
from pyff.kitchensink import hl


LOGGER = logging.getLogger(__name__)


class ModuleSummary:  # pylint: disable=too-few-public-methods
    """Holds summary information about a module"""

    def __init__(self, name: str, node: ast.Module) -> None:
        self.name: str = name
        self.node: ast.Module = node


class ModulePyfference:  # pylint: disable=too-few-public-methods
    """Holds differences between two Python modules"""

    def __init__(
        self,
        imports: Optional[pi.ImportsPyfference] = None,
        classes: Optional[pc.ClassesPyfference] = None,
        functions: Optional[pf.FunctionsPyfference] = None,
    ) -> None:

        self.other: List = []
        self.imports: Optional[pi.ImportsPyfference] = imports
        self.classes: Optional[pc.ClassesPyfference] = classes
        self.functions: Optional[pf.FunctionsPyfference] = functions

    def __str__(self):
        changes = [self.imports, self.classes, self.functions] + self.other
        return "\n".join([str(change) for change in changes if change is not None])

    def simplify(self) -> Optional["ModulePyfference"]:
        """Cleans empty differences, empty sets etc. after manipulation"""
        if self.imports is not None:
            self.imports = self.imports.simplify()

        if self.classes is not None:
            self.classes = self.classes.simplify()

        if self.functions is not None:
            self.functions = self.functions.simplify()

        return self if (self.functions or self.classes or self.imports or self.other) else None


class ModulesPyfference:  # pylint: disable=too-few-public-methods
    """Holds difference between modules in a package"""

    def __init__(
        self,
        removed: Dict[str, ModuleSummary],
        changed: Dict[str, ModulePyfference],
        new: Dict[str, ModuleSummary],
    ) -> None:
        self.removed: Dict[str, ModuleSummary] = removed
        self.changed: Dict[str, ModulePyfference] = changed
        self.new: Dict[str, ModuleSummary] = new

    def __str__(self):
        return "\n".join(
            [
                f"Module {hl(module)} changed:\n  " + str(change).replace("\n", "\n  ")
                for module, change in self.changed.items()
            ]
        )

    def __repr__(self):
        return (
            f"ModulesPyfference(removed={repr(self.removed)}, "
            f"changed={repr(self.changed)}, new={repr(self.new)})"
        )

    def __bool__(self):
        return bool(self.removed or self.changed or self.new)


def pyff_module(old: ast.Module, new: ast.Module) -> Optional[ModulePyfference]:
    """Return difference between two Python modules, or None if they are identical"""
    old_imports = pi.ImportedNames.extract(old)
    new_imports = pi.ImportedNames.extract(new)
    imports = pi.pyff_imports(old, new)
    classes = pc.pyff_classes(old, new, old_imports, new_imports)
    functions = pf.pyff_functions(old, new, old_imports, new_imports)

    if imports or classes or functions:
        LOGGER.debug("Modules differ")
        pyfference = ModulePyfference(imports, classes, functions)
        return pyfference

    LOGGER.debug("Modules are identical")
    return None


def pyff_module_code(old: str, new: str) -> Optional[ModulePyfference]:
    """Return difference between two Python modules, or None if they are identical"""
    # pylint: disable=unused-variable
    old_ast = ast.parse(old)
    new_ast = ast.parse(new)
    return pyff_module(old_ast, new_ast)
