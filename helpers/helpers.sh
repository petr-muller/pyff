#!/bin/bash

. v/bin/activate

example() {
  pyff tests/examples/$1*.old tests/examples/$1*.new
}

example_package() {
  pyff-package tests/package-examples/old/$1 tests/package-examples/new/$1
}

extest() {
    helpers/clitest --prefix '# ' --diff-options '-u --color=always' tests/examples/$1*.new
}

extest_package() {
    helpers/clitest --prefix '# ' --diff-options '-u --color=always' tests/package-examples/$1.clitest
}
exdebug() {
  pyff tests/examples/$1*.old tests/examples/$1*.new  --debug
}

exdebug_package() {
  pyff-package tests/package-examples/old/$1 tests/package-examples/new/$1 --debug
}

exdiff() {
  vimdiff tests/examples/$1*.old tests/examples/$1*.new
}

example_quotes() {
  pyff --highlight-names quotes tests/examples/$1*.old tests/examples/$1*.new
}

example_package_quotes() {
  pyff-package --highlight-names quotes tests/package-examples/old/$1 tests/package-examples/new/$1
}

exdebug_package_quotes() {
  pyff-package --highlight-names quotes tests/package-examples/old/$1 tests/package-examples/new/$1 --debug
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
    helpers/clitest --prefix '# ' --diff-options '-u --color=always' tests/examples/*.new &&
    helpers/clitest --prefix '# ' --diff-options '-u --color=always' tests/package-examples/*.clitest
}

cov() {
  ft && firefox htmlcov/index.html
}
