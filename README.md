# pyff: Python Diff

Python Diff compares two versions of Python code (modules, packages,
directories containing Python modules and/or packages) and detects syntactical
and semantical differences between them.

[![Build Status](https://travis-ci.org/petr-muller/pyff.svg?branch=master)](https://travis-ci.org/petr-muller/pyff) [![Maintainability](https://api.codeclimate.com/v1/badges/bb1aa4b86fed8097aa0f/maintainability)](https://codeclimate.com/github/petr-muller/pyff/maintainability) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/b970a7c6c6314ab3b28bddaeab523457)](https://www.codacy.com/app/afri/pyff?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=petr-muller/pyff&amp;utm_campaign=Badge_Grade) [![Coverage Status](https://coveralls.io/repos/github/petr-muller/pyff/badge.svg?branch=master)](https://coveralls.io/github/petr-muller/pyff?branch=master)

## Installation

You can install pyff from [Python Package Index](https://pypi.org/) as
`pythodiff` (unfortunately, a name `pyff` was taken already):

```
pip install pythondiff
```

## Usage

You can run `pyff` to compare two Python modules:

```
pyff old.py new.py
```

For comparing Python packages, there is the `pyff-package` executable:

```
pyff-package old_package new_package
```

You can also compare directories using the `pyff-dir` executable. In this case,
`pyff` finds all Python content in both directories (recurively) and compares
everything it finds:

```
pyff-dir old_directory new_directory
```

Finally, `pyff-git` can compare Python content between two revisions in a given
Git repository. As with the `pyff-dir` case, this finds all Python content in
the repository.

```
pyff-git https://github.com/petr-muller/pyff.git master^ master
```

## Development

The development of `pyff` is far from complete: most of the basic features (code
elements being removed, changed or added) are there but not all of them. Some
Python code can also confuse `pyff` or even make it crash. PRs or issue reports
are happily accepted.

`pyff` is written using a modern (3.6+) Python version and has both unit and
integration tests. The unit test coverage goal is 100% but it is OK to not cover
some elementary (or really hard to unit-test) code, provided the code is marked
with a `# pragma: no cover` comment. [pytest](https://pytest.org) is used as a
unit test driver. All code is statically checked with
[Pylint](https://www.pylint.org/) and also annotated with Python type hints. The
[mypy](http://mypy-lang.org/) checker is used to check them. You can install all
necessary test requirements using pip:

```
pip install -r requirements-tests.txt
```

There are shell helpers in `helpers/helpers.sh` that make
executing all checks easier:

```
$ . helpers/helpers.sh
$ ft # Fast Test: run just unit tests, without pylint and mypy checks
$ st # Slow Test: run all (unit and integration) tests, pylint and mypy
```

The integration tests are executed using an excellent
[clitest](https://github.com/aureliojargas/clitest) tool.

## Future

`pyff` is a pre-1.0.0 version: basically a toy project of mine. A brief list of
TODOs for me to consider doing a 1.0.0 version is in [#19](#19). My idea is to
bring `pyff` to a small GitHub PR-commenting bot that would comment PRs to
Python repositories with a nice, human-readable summary of changes.
