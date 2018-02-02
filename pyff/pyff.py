"""Functions for comparison of various Python entities"""

from ast import FunctionDef, parse
from typing import cast
from pyff.pyfference import FunctionPyfference

def _pyff_function_ast(first: FunctionDef, second: FunctionDef) -> FunctionPyfference:
    """Return differences between two Python function ASTs, or None if they are identical"""
    if first.name == second.name:
        return None

    return FunctionPyfference(names=(first.name, second.name))

def pyff_function(first: str, second: str) -> FunctionPyfference:
    """Return differences between two Python functions, or None if they are identical"""
    first_ast = parse(first).body
    second_ast = parse(second).body

    if len(first_ast) != 1 or not isinstance(first_ast[0], FunctionDef):
        raise ValueError(f"First argument does not seem to be a single Python function: {first}")
    if len(second_ast) != 1 or not isinstance(second_ast[0], FunctionDef):
        raise ValueError(f"Second argument does not seem to be a single Python function: {second}")


    return _pyff_function_ast(cast(FunctionDef, first_ast[0]), cast(FunctionDef, second_ast[0]))
