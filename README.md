# pyff: Python Diff

The purpose of Python Diff (`pyff`) is to compare two versions of a Python module
and detect syntactical and semantical differences between them. Currently `pyff`
is a very early-stage, experimental toy project, so please do not expect miracles.

[![Build Status](https://travis-ci.org/petr-muller/pyff.svg?branch=master)](https://travis-ci.org/petr-muller/pyff) [![Maintainability](https://api.codeclimate.com/v1/badges/bb1aa4b86fed8097aa0f/maintainability)](https://codeclimate.com/github/petr-muller/pyff/maintainability) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/b970a7c6c6314ab3b28bddaeab523457)](https://www.codacy.com/app/afri/pyff?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=petr-muller/pyff&amp;utm_campaign=Badge_Grade) [![Coverage Status](https://coveralls.io/repos/github/petr-muller/pyff/badge.svg?branch=master)](https://coveralls.io/github/petr-muller/pyff?branch=master)

## Usage

You can install `pyff`, preferably to a virtual environment, using the `setup.py`
file.

```
$ python -m venv venv
$ . venv/bin/activate
$ pip install -r requirements.txt
$ python setup.py install
(...)
```

This installs the `pyff` executable that accepts two Python files as positional
arguments:

```
$ pyff tests/examples/01-run.old tests/examples/01-run.new
Added import of new names ArgumentParser, Action from new package argparse
New class ParsePlayerAction with 0 public methods
Function main changed implementation, newly uses external names ArgumentParser
```

Programmatical interface in the form of `pyff.api` or something similar is on
the roadmap.

## Development

Currently, `pyff` is quite trivial, but one of my goals while working on it was
to try use various Python development support tools, sometimes quite
excessively: [pytest](https://pytest.org) is used for testing (along with few
plugins) and [Pylint](https://www.pylint.org/) for static analysis. The code of
`pyff` is annotated with Python type hints and [mypy](http://mypy-lang.org/) is
used to check them. There are shell helpers in `helpers/helpers.sh` that make
executing all checks easier:

```
$ pip install -r requirements-tests.txt
$ . helpers/helpers.sh
$ ft # Fast Test: run all tests without coverage, pylint and mypy check
$ st # Slow Test: run all tests with coverage, pylint and mypy
```

## Future

Currently, the high-level roadmap looks somewhat like this:

1. Finish the `pyff` command and provide basic set of smart comparisons.
2. Provide programmatical API (allow `import pyff.api`) providing
   machine-readable difference artifact.
3. Build a Git-aware comparison tools that will be able to compare Git revisions
   (instead of single files)
4. Build a PR-commenting GitHub bot that should provide human readable, natural
   language "summaries" to submitted Python project PRs.
