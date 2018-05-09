"""Contains class with summary information about various Python entities"""

from typing import List, Union, Optional
from pyff.kitchensink import HL_OPEN, HL_CLOSE

class LocalBaseClass:
    # pylint: disable=too-few-public-methods
    """Represents part of a class summary for case when base class is local"""
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"local {HL_OPEN}{self.name}{HL_CLOSE}"

class ImportedBaseClass:
    # pylint: disable=too-few-public-methods
    """Represents part of a class summary for case when base class is imported"""
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"imported {HL_OPEN}{self.name}{HL_CLOSE}"

BaseClassType = Union[LocalBaseClass, ImportedBaseClass] # pylint: disable=invalid-name

class ClassSummary(): # pylint: disable=too-few-public-methods
    """Contains summary information about a class"""
    def __init__(self, name: str, methods: int, private: int,
                 baseclasses: Optional[List[BaseClassType]] = None) -> None:
        self.name: str = name
        self.methods: int = methods
        self.private_methods: int = private
        self.public_methods: int = methods - private
        self.baseclasses: Optional[List[BaseClassType]] = baseclasses

    def __str__(self) -> str:
        class_part: str = f"class {HL_OPEN}{self.name}{HL_CLOSE}"
        method_part: str = f"with {self.public_methods} public methods"

        if not self.baseclasses:
            return f"{class_part} {method_part}"
        elif len(self.baseclasses) == 1:
            return f"{class_part} derived from {str(self.baseclasses[0])} {method_part}"

        raise Exception("Multiple inheritance not yet implemented")

class FunctionSummary(): # pylint: disable=too-few-public-methods
    """Contains summary information about a function"""
    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self):
        return f"function {HL_OPEN}{self.name}{HL_CLOSE}"
