"""This module contains code that handles comparing modules"""

import ast
import logging
from typing import List, Optional

import pyff.classes as pc
import pyff.functions as pf
import pyff.imports as pi


LOGGER = logging.getLogger(__name__)


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
