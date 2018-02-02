# pylint: disable=missing-docstring

from pyff.pyfference import FunctionPyfference

def test_function_name_changed():
    fpyff = FunctionPyfference(names=("first", "second"))
    assert fpyff.name.old == "first"
    assert fpyff.name.new == "second"
    assert len(fpyff) == 1

def test_function_name_same():
    fpyff = FunctionPyfference()
    assert fpyff.name is None
    assert len(fpyff) == 0  # pylint: disable=len-as-condition
