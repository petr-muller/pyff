"""Python diff"""

import setuptools
import pyff

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

setuptools.setup(
    name="pythondiff",
    version=pyff.__version__,
    description="Python Diff",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/petr-muller/pyff",
    author="Petr Muller",
    author_email="afri@afri.cz",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ],
    keywords="python static_analysis diff",
    packages=["pyff"],
    setup_requires=["pytest-runner", "pytest-bdd", "pytest-pylint", "pytest-mypy", "pytest-cov"],
    tests_require=["pytest", "pylint", "mypy"],
    install_requires=["colorama"],
    entry_points={"console_scripts": ["pyff=pyff.run:pyffmod", "pyff-package=pyff.run:pyffpkg"]},
)
