#!/bin/bash

. v/bin/activate

example() {
  pyff tests/examples/$1*.old tests/examples/$1*.new
}

exdebug() {
  pyff tests/examples/$1*.old tests/examples/$1*.new  --debug
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
    pylint --rcfile=.pylintrc pyff tests/unit/*.py &&
    mypy pyff &&
    helpers/clitest --prefix '# ' --diff-options '-u --color=always' tests/examples/*.new
}

cov() {
  ft && firefox htmlcov/index.html
}
