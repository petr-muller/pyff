# pylint: disable=missing-docstring, no-self-use, too-few-public-methods

import os
import pathlib
from unittest.mock import MagicMock, patch

import pyff.directories as pd
import pyff.repositories as pr


class TestRevisionsPyfference:
    def test_sanity(self):
        directory_change = MagicMock(spec=pd.DirectoryPyfference)
        directory_change.__str__.return_value = "le change"
        change = pr.RevisionsPyfference(change=directory_change)

        assert str(change) == "le change"


class TestPyffGitRevision:
    @staticmethod
    def _make_fake_clone(fs, revisions):  # pylint: disable=invalid-name
        def _fake_clone_method(_, directory):
            fs.create_dir(directory)
            fake_repo = MagicMock()

            def _fake_checkout(revision):
                if revision in revisions:
                    oldcwd = os.getcwd()
                    os.chdir(directory)
                    revisions[revision]()
                    os.chdir(oldcwd)

            fake_repo.git.checkout = _fake_checkout
            return fake_repo

        return _fake_clone_method

    def test_difference(self, fs):  # pylint: disable=invalid-name
        def checkout_old():
            fs.create_file("old_package/__init__.py")

        def checkout_new():
            fs.create_file("package/__init__.py")

        with patch("git.Repo.clone_from") as fake_clone:

            fake_clone.side_effect = self._make_fake_clone(
                fs, {"old": checkout_old, "new": checkout_new}
            )
            change = pr.pyff_git_revision("repo", "old", "new")
            assert change is not None
            assert pathlib.Path("package") in change.packages.new

    def test_identical(self, fs):  # pylint: disable=invalid-name
        def checkout_old():
            fs.create_file("package/__init__.py")

        with patch("git.Repo.clone_from") as fake_clone:
            fake_clone.side_effect = self._make_fake_clone(fs, {"old": checkout_old})
            change = pr.pyff_git_revision("repo", "old", "new")
            assert change is None
