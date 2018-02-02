"""Python diff"""

from setuptools import setup

setup(
    name="pyff",
    version="0.0.0",
    description="Python Diff",
    # long_description=
    # url=
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
    packages=['pyff'],
    setup_requires=['pytest-runner', 'pytest-bdd', 'pytest-pylint', 'pytest-mypy', 'pytest-cov'],
    tests_require=['pytest', 'pylint', 'mypy'],
    install_requires=[],
    # entry_points=
)
