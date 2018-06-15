"""Testing helpers"""

import ast
import pyff.imports as pi
import pyff.functions as pf


def parse_imports(code: str) -> pi.ImportedNames:
    """Parse import statement and create pi.ImportedNames object for it"""
    extractor = pi.ImportExtractor()
    extractor.visit(ast.parse(code))
    return extractor.names


def extract_names_from_function(code: str, imported_names: pi.ImportedNames):
    """Parse function definition and extract external name usage from it"""
    extractor = pf.ExternalNamesExtractor(imported_names)
    extractor.visit(ast.parse(code))
    return extractor.names
