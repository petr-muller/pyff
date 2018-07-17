"""This module contains code that handles comparing revisions in Git repository"""

import tempfile
import shutil
import pathlib
from typing import Optional
import git


import pyff.directories as pd
import pyff.packages as pp


class RevisionsPyfference:  # pylint: disable=too-few-public-methods
    """Represents a difference between two revisions"""

    # RevisionsPyfference is basically the same as DirectoryPyfference, so we
    # embed DirectoryPyfference and delegate everything to it
    def __init__(self, change: pd.DirectoryPyfference) -> None:
        self._change: pd.DirectoryPyfference = change

    def __str__(self):
        return str(self._change)

    @property
    def packages(self) -> Optional[pp.PackagesPyfference]:
        """Return what Python packages differ between revisions"""
        return self._change.packages


def pyff_git_revision(repository: str, old: str, new: str) -> Optional[RevisionsPyfference]:
    """Compare two revisions in a Git repository"""
    with tempfile.TemporaryDirectory() as temporary_wd:
        working_directory = pathlib.Path(temporary_wd)
        source_dir = working_directory / "source"
        old_dir = working_directory / "old"
        new_dir = working_directory / "new"

        repo = git.Repo.clone_from(repository, source_dir)

        repo.git.checkout(old)
        shutil.copytree(source_dir, old_dir)

        repo.git.checkout(new)
        shutil.copytree(source_dir, new_dir)

        change = pd.pyff_directory(old_dir, new_dir)
        if change:
            return RevisionsPyfference(change)

        return None
