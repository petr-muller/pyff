# pylint: disable=missing-docstring

from pyff.summary import ClassSummary

def test_class_summary():
    cls = ClassSummary("classname", methods=5, private=2)
    assert cls.name == "classname"
    assert cls.methods == 5
    assert cls.private_methods == 2
    assert cls.public_methods == 3
    assert str(cls) == "class 'classname' with 3 public methods"
