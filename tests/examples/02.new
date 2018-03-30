"""Log of a single VtES game"""

from typing import Sequence

class Game:
    """Represents a VtES game"""
    # pylint: disable=too-few-public-methods
    def __init__(self, table: Sequence[str]) -> None:
        self.table: Sequence[str] = table

    def __str__(self) -> str:
        return " \u25b6 ".join(self.table)
