#!/bin/bash

example() {
  pyff tests/examples/$1*.old tests/examples/$1*.new
}

exdiff() {
  vimdiff tests/examples/$1*.old tests/examples/$1*.new
}

example_quotes() {
  pyff --highlight-names quotes tests/examples/$1*.old tests/examples/$1*.new
}

ft() {
  cat helpers/fast-setup.cfg > setup.cfg
  python setup.py test
}

st() {
  cat helpers/strict-setup.cfg > setup.cfg
  python setup.py test &&
    helpers/clitest --prefix '# ' --diff-options '-u --color=always' tests/examples/*.new &&
    mypy pyff
}

cov() {
  ft && firefox htmlcov/index.html
}
