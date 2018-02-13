"""Contains class with summary information about various Python entities"""

class ClassSummary(): # pylint: disable=too-few-public-methods
    """Contains summary information about a class"""
    def __init__(self, name: str, methods: int, private: int) -> None:
        self.name: str = name
        self.methods: int = methods
        self.private_methods: int = private
        self.public_methods: int = methods - private

    def __str__(self) -> str:
        return f"class '{self.name}' with {self.public_methods} public methods"
