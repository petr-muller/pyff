# pylint: disable=missing-docstring, no-self-use, too-few-public-methods
import pathlib
from unittest.mock import MagicMock
import pytest
import pyff.modules as pm
import pyff.packages as pp


class TestPackagePyfference:
    def test_sanity(self):
        mock_modules = MagicMock(spec=pm.ModulesPyfference)
        mock_modules.__str__.return_value = "Modules Pyfference"
        change = pp.PackagePyfference(modules=mock_modules)
        assert change.modules is not None
        assert str(change) == "Modules Pyfference"


class TestExtractions:
    def test_extract_module(self):
        assert pp.extract_modules(
            [pathlib.Path("a/b.py"), pathlib.Path("a/b/c.py")], pathlib.Path("a")
        ) == {"b.py"}
        assert (
            pp.extract_modules(
                [pathlib.Path("a/b/b.py"), pathlib.Path("a/b/c.py")], pathlib.Path("a")
            )
            == frozenset()
        )


class TestPyffPackage:
    @pytest.fixture
    def sample_package(self, fs):  # pylint: disable=invalid-name
        fs.create_dir("pkg")
        fs.create_file("pkg/__init__.py")
        fs.create_file("pkg/module.py")

        return pathlib.Path("pkg")

    @pytest.fixture
    def sample_with_new_module(self, fs):  # pylint: disable=invalid-name
        fs.create_dir("pkg_new")
        fs.create_file("pkg_new/__init__.py")
        fs.create_file("pkg_new/module.py")
        fs.create_file("pkg_new/new.py")
        return pathlib.Path("pkg_new")

    def test_identical(self, sample_package):
        assert pp.pyff_package(sample_package, sample_package) is None

    def test_new_module(self, sample_package, sample_with_new_module):
        change = pp.pyff_package(sample_package, sample_with_new_module)
        assert change is not None
        assert change.modules is not None
        assert "new.py" in change.modules.new
