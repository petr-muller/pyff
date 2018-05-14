"""Placeholders for various elements in output"""
HL_OPEN = "``"
HL_CLOSE = "''"

def hl(what: str) -> str: # pylint: disable=invalid-name
    """Return highlighted string"""
    return f"{HL_OPEN}{what}{HL_CLOSE}"
