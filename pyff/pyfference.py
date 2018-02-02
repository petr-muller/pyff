"""Classes holding information about differences between individual Python elements"""
from collections import namedtuple
from typing import Tuple, List

Change = namedtuple("Change", ["old", "new"])

class FunctionPyfference:  # pylint: disable=too-few-public-methods
    """Holds differences between Python function definitions"""
    def __init__(self, names: Tuple[str, str] = None) -> None:
        self.name: Change = None
        self.changes: List[Change] = []

        if names:
            self.name = Change(names[0], names[1])
            self.changes.append(self.name)

    def __len__(self):
        return len(self.changes)
