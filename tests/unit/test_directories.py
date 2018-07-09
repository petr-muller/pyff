# pylint: disable=missing-docstring, no-self-use, too-few-public-methods

import pathlib
from unittest.mock import MagicMock
import pytest
import pyff.packages as pp
import pyff.directories as pd


class TestDirectoryPyfference:
    def test_packages(self):
        mock_packages = MagicMock(spec=pp.PackagesPyfference)
        mock_packages.__str__.return_value = "Packages differ"
        change = pd.DirectoryPyfference(packages=mock_packages)
        assert change
        assert change.packages
        assert str(change) == "Packages differ"

    def test_empty(self):
        change = pd.DirectoryPyfference(packages=None)
        assert not change
        assert str(change) == ""


class TestFindThosePythonz:
    def test_package(self, fs):  # pylint: disable=invalid-name
        fs.create_file("toplevel/package/__init__.py")

        packages, _ = pd.find_those_pythonz(pathlib.Path("toplevel"))
        assert packages == {pathlib.Path("package")}

    def test_only_toplevel_package(self, fs):  # pylint: disable=invalid-name
        fs.create_file("toplevel/package/__init__.py")
        fs.create_file("toplevel/package/subpackage/__init__.py")

        packages, _ = pd.find_those_pythonz(pathlib.Path("toplevel"))
        assert packages == {pathlib.Path("package")}

    def test_package_somewhere_deep(self, fs):  # pylint: disable=invalid-name
        fs.create_file("toplevel/somewhere/really/deep/is/a/package/__init__.py")

        packages, _ = pd.find_those_pythonz(pathlib.Path("toplevel"))
        assert packages == {pathlib.Path("somewhere/really/deep/is/a/package")}

    def test_ignore_nonpython_stuff(self, fs):  # pylint: disable=invalid-name
        fs.create_file("toplevel/package/__init__.py")
        fs.create_file("toplevel/README")
        fs.create_file("toplevel/deeper/some-legacy-c-stuff.c")

        packages, _ = pd.find_those_pythonz(pathlib.Path("toplevel"))
        assert packages == {pathlib.Path("package")}

    def test_module(self, fs):  # pylint: disable=invalid-name
        fs.create_file("toplevel/module.py")
        _, modules = pd.find_those_pythonz(pathlib.Path("toplevel"))
        assert modules == {pathlib.Path("module.py")}

    def test_module_deep(self, fs):  # pylint: disable=invalid-name
        fs.create_file("toplevel/somewhere/deep/is/a/module.py")
        _, modules = pd.find_those_pythonz(pathlib.Path("toplevel"))
        assert modules == {pathlib.Path("somewhere/deep/is/a/module.py")}

    def test_everything(self, fs):  # pylint: disable=invalid-name
        fs.create_file("toplevel/package/__init__.py")
        fs.create_file("toplevel/somewhere/really/deep/is/a/package/__init__.py")
        fs.create_file("toplevel/module.py")
        fs.create_file("toplevel/somewhere/deep/is/a/module.py")

        packages, modules = pd.find_those_pythonz(pathlib.Path("toplevel"))
        assert packages == {
            pathlib.Path("somewhere/really/deep/is/a/package"),
            pathlib.Path("package"),
        }
        assert modules == {pathlib.Path("somewhere/deep/is/a/module.py"), pathlib.Path("module.py")}


class TestPyffDirectory:
    def test_identical(self, fs):  # pylint: disable=invalid-name
        fs.create_file("old/package/__init__.py")
        fs.create_file("new/package/__init__.py")

        assert pd.pyff_directory(pathlib.Path("old"), pathlib.Path("new")) is None

    def test_invalid(self, fs):  # pylint: disable=invalid-name
        fs.create_file("old")
        fs.create_file("dir/pkg/__init__.py")

        with pytest.raises(ValueError):
            pd.pyff_directory(pathlib.Path("old"), pathlib.Path("dir"))

        with pytest.raises(ValueError):
            pd.pyff_directory(pathlib.Path("dir"), pathlib.Path("old"))

        with pytest.raises(ValueError):
            pd.pyff_directory(pathlib.Path("dir"), pathlib.Path("nonexistent"))

    def test_remove_package(self, fs):  # pylint: disable=invalid-name
        fs.create_file("old/pkg/__init__.py")
        fs.create_dir("new")
        change = pd.pyff_directory(pathlib.Path("old"), pathlib.Path("new"))
        assert change
        assert pathlib.Path("pkg") in change.packages.removed

    def test_add_package(self, fs):  # pylint: disable=invalid-name
        fs.create_dir("old")
        fs.create_file("new/pkg/__init__.py")
        change = pd.pyff_directory(pathlib.Path("old"), pathlib.Path("new"))
        assert change
        assert pathlib.Path("pkg") in change.packages.new

    def test_changed_package(self, fs):  # pylint: disable=invalid-name
        fs.create_dir("old/pkg/__init__.py")
        fs.create_file("new/pkg/__init__.py")
        fs.create_file("new/pkg/module.py")
        change = pd.pyff_directory(pathlib.Path("old"), pathlib.Path("new"))
        assert change
        assert pathlib.Path("pkg") in change.packages.changed
