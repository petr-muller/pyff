# pylint: disable=missing-docstring, no-self-use, too-few-public-methods
import pathlib
from unittest.mock import MagicMock
import pytest
import pyff.modules as pm
import pyff.packages as pp


class TestPackagesPyfference:
    def test_empty(self):
        assert not pp.PackagesPyfference(None, None, None)

    def test_removed(self):
        path = pathlib.Path("path/to/package")
        summary = pp.PackageSummary(path)
        change = pp.PackagesPyfference(removed={path: summary}, changed=None, new=None)
        assert change
        assert path in change.removed
        assert str(change) == "Removed package ``path/to/package''"

    def test_new(self):
        path = pathlib.Path("path/to/package")
        summary = pp.PackageSummary(path)
        change = pp.PackagesPyfference(new={path: summary}, changed=None, removed=None)
        assert change
        assert path in change.new
        assert str(change) == "New package ``path/to/package''"

    def test_changed(self):
        path = pathlib.Path("path/to/package")
        inner_change = MagicMock(spec=pp.PackagePyfference)
        inner_change.__str__.return_value = "Total rewrite"
        change = pp.PackagesPyfference(changed={path: inner_change}, removed=None, new=None)
        assert change
        assert path in change.changed
        assert str(change) == "Package ``path/to/package'' changed:\n  Total rewrite"


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
            [pathlib.Path("a/b.py"), pathlib.Path("a/b/c.py")],
            pp.summarize_package(pathlib.Path("a")),
        ) == {"b.py"}
        assert (
            pp.extract_modules(
                [pathlib.Path("a/b/b.py"), pathlib.Path("a/b/c.py")],
                pp.summarize_package(pathlib.Path("a")),
            )
            == frozenset()
        )


class TestPyffPackage:
    @pytest.fixture
    def sample_package_path(self, fs):  # pylint: disable=invalid-name
        fs.create_dir("pkg")
        fs.create_file("pkg/__init__.py")
        fs.create_file("pkg/module.py")

        return pathlib.Path("pkg")

    @pytest.fixture
    def sample_with_new_module_path(self, fs):  # pylint: disable=invalid-name
        fs.create_dir("pkg_new")
        fs.create_file("pkg_new/__init__.py")
        fs.create_file("pkg_new/module.py")
        fs.create_file("pkg_new/new.py")

        return pathlib.Path("pkg_new")

    @pytest.fixture
    def sample_package(self, sample_package_path):  # pylint: disable=invalid-name
        return pp.summarize_package(sample_package_path)

    @pytest.fixture
    def sample_with_new_module(self, sample_with_new_module_path):  # pylint: disable=invalid-name
        return pp.summarize_package(sample_with_new_module_path)

    def test_identical(self, sample_package):
        assert pp.pyff_package(sample_package, sample_package) is None

    def test_new_module(self, sample_package, sample_with_new_module):
        change = pp.pyff_package(sample_package, sample_with_new_module)
        assert change is not None
        assert change.modules is not None
        assert "new.py" in change.modules.new

    def test_pyff_package_path(self, sample_package_path, sample_with_new_module_path):
        change = pp.pyff_package_path(sample_package_path, sample_with_new_module_path)
        assert change is not None
        assert change.modules is not None
        assert "new.py" in change.modules.new
