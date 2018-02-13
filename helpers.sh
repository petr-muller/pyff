example() {
  pyff tests/examples/$1*.old tests/examples/$1*.new
}

ft() {
  cat fast-setup.cfg > setup.cfg
  python setup.py test
}

st() {
  cat strict-setup.cfg > setup.cfg
  python setup.py test
}
