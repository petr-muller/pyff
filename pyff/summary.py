"""Contains class with summary information about various Python entities"""

from pyff.kitchensink import HL_OPEN, HL_CLOSE

class ClassSummary(): # pylint: disable=too-few-public-methods
    """Contains summary information about a class"""
    def __init__(self, name: str, methods: int, private: int) -> None:
        self.name: str = name
        self.methods: int = methods
        self.private_methods: int = private
        self.public_methods: int = methods - private

    def __str__(self) -> str:
        return f"class {HL_OPEN}{self.name}{HL_CLOSE} with {self.public_methods} public methods"
