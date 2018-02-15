"""Functions for comparison of various Python entities"""

from ast import FunctionDef, parse, NodeVisitor, Module, dump
from typing import cast, Set, Dict, Iterable
from collections import defaultdict
from itertools import zip_longest

import pyff.pyfference as pf
from pyff.summary import ClassSummary

class ExternalNamesExtractor(NodeVisitor):
    """Collects information about imported name usage in function"""
    def __init__(self, imported_names: Iterable[str]) -> None:
        self.imported_names: Iterable[str] = imported_names
        self.names: Set[str] = set()

    def visit_Name(self, node): # pylint: disable=invalid-name
        """Compare all names against a list of imported names"""
        if node.id in self.imported_names:
            self.names.add(node.id)

def _compare_import_usage(old: FunctionDef, new: FunctionDef,
                          old_imports: Iterable[str] = None,
                          new_imports: Iterable[str] = None) -> Iterable[str]:
    first_walker = ExternalNamesExtractor(old_imports)
    second_walker = ExternalNamesExtractor(new_imports)

    first_walker.visit(old)
    second_walker.visit(new)

    appeared = second_walker.names - first_walker.names

    return appeared

def _pyff_function_ast(first: FunctionDef, second: FunctionDef,
                       old_imports: Iterable[str] = None,
                       new_imports: Iterable[str] = None) -> pf.FunctionPyfference:
    """Return differences between two Python function ASTs, or None if they are identical"""
    names = None
    if first.name != second.name:
        names = (first.name, second.name)

    implementation = None
    for old_statement, new_statement in zip_longest(first.body, second.body):
        if dump(old_statement) != dump(new_statement):
            implementation = True
            break

    if old_imports or new_imports:
        appeared_import_usage = _compare_import_usage(first, second, old_imports, new_imports)
    else:
        appeared_import_usage = None

    if names or implementation:
        return pf.FunctionPyfference(name=first.name, names=names, implementation=implementation,
                                     appeared_import_usage=appeared_import_usage)

    return None

def _pyff_from_imports(first_ast: Module, second_ast: Module) -> pf.FromImportPyfference:
    """Return differences in `from X import Y` statements in two modules"""
    first_walker = ImportFromExtractor()
    second_walker = ImportFromExtractor()

    first_walker.visit(first_ast)
    second_walker.visit(second_ast)

    appeared = set(second_walker.modules.keys()) - set(first_walker.modules.keys())
    new = {}
    for module in appeared:
        new[module] = second_walker.modules[module]

    return pf.FromImportPyfference(new) if new else None

class ClassesExtractor(NodeVisitor):
    """Extracts information about classes in a module"""
    def __init__(self) -> None:
        self.classes: Set[ClassSummary] = set()
        self._private_methods: int = 0
        self._methods: int = 0

    def visit_ClassDef(self, node): # pylint: disable=invalid-name
        """Save information about classes that appeared in a module"""
        self._private_methods: int = 0
        self._methods: int = 0
        self.generic_visit(node)
        self.classes.add(ClassSummary(node.name, self._methods, self._private_methods))

    def visit_FunctionDef(self, node): # pylint: disable=invalid-name
        """Save counts of encountered private/public methods"""
        if node.name.startswith("_"):
            self._private_methods += 1
        self._methods += 1

def _pyff_classes(first_ast: Module, second_ast: Module) -> pf.ClassesPyfference:
    """Return differences in classes defined in two modules"""
    first_walker = ClassesExtractor()
    second_walker = ClassesExtractor()

    first_walker.visit(first_ast)
    second_walker.visit(second_ast)

    appeared = second_walker.classes - first_walker.classes

    return pf.ClassesPyfference(appeared) if appeared else None

class MethodsExtractor(NodeVisitor):
    """Extract information about methods in a module"""
    def __init__(self) -> None:
        self.names: Set[str] = set()
        self.functions: Dict[str, FunctionDef] = {}
        self.imported_names: Set[str] = set()

    def visit_ImportFrom(self, node): # pylint: disable=invalid-name
        """Save imported names"""
        for name in node.names:
            self.imported_names.add(name.name)

    def visit_ClassDef(self, node): # pylint: disable=invalid-name
        """Prevent this visitor from inspecting classes"""
        pass

    def visit_FunctionDef(self, node): # pylint: disable=invalid-name
        """Save top-level function definitions"""
        self.names.add(node.name)
        self.functions[node.name] = node

def _pyff_functions(first_ast: Module, second_ast: Module) -> pf.FunctionsPyfference:
    """Return differences in top-level functions in two modules"""
    first_walker = MethodsExtractor()
    second_walker = MethodsExtractor()

    first_walker.visit(first_ast)
    second_walker.visit(second_ast)

    both = first_walker.names.intersection(second_walker.names)
    differences = {}
    for function in both:
        difference = _pyff_function_ast(first_walker.functions[function],
                                        second_walker.functions[function],
                                        first_walker.imported_names,
                                        second_walker.imported_names)
        if difference:
            differences[function] = difference

    return pf.FunctionsPyfference(changed=differences) if differences else None


def _pyff_modules(first_ast: Module, second_ast: Module) -> pf.ModulePyfference:
    from_imports = _pyff_from_imports(first_ast, second_ast)
    classes = _pyff_classes(first_ast, second_ast)
    functions = _pyff_functions(first_ast, second_ast)

    if from_imports or classes or functions:
        return pf.ModulePyfference(from_imports, classes, functions)

    return None

class ImportFromExtractor(NodeVisitor):
    """Extracts information about `from x import y` statements"""
    def __init__(self):
        self.modules = defaultdict(set)
        super(ImportFromExtractor, self).__init__()

    def visit_ImportFrom(self, node): # pylint: disable=invalid-name
        """Save information about `from x import y` statements"""
        self.modules[node.module].update([node.name for node in node.names])

def pyff_function(first: str, second: str,
                  old_imports: Iterable[str] = None,
                  new_imports: Iterable[str] = None) -> pf.FunctionPyfference:
    """Return differences between two Python functions, or None if they are identical"""
    first_ast = parse(first).body
    second_ast = parse(second).body

    if len(first_ast) != 1 or not isinstance(first_ast[0], FunctionDef):
        raise ValueError(f"First argument does not seem to be a single Python function: {first}")
    if len(second_ast) != 1 or not isinstance(second_ast[0], FunctionDef):
        raise ValueError(f"Second argument does not seem to be a single Python function: {second}")

    return _pyff_function_ast(cast(FunctionDef, first_ast[0]), cast(FunctionDef, second_ast[0]),
                              old_imports, new_imports)

def pyff_module(first: str, second: str) -> pf.ModulePyfference:
    """Return difference between two Python modules, or None if they are identical"""
    # pylint: disable=unused-variable
    first_ast = parse(first)
    second_ast = parse(second)
    return _pyff_modules(first_ast, second_ast)
