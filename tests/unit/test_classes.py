# pylint: disable=missing-docstring, no-self-use, too-few-public-methods

import ast
from pytest import raises, fixture
import pyff.classes as pc
from helpers import parse_imports

class TestClassSummary():
    def test_class_summary(self):
        cls = pc.ClassSummary("classname", methods=5, private=2)
        assert cls.name == "classname"
        assert cls.methods == 5
        assert cls.private_methods == 2
        assert cls.public_methods == 3
        assert str(cls) == "class ``classname'' with 3 public methods"

    def test_singular(self):
        cls = pc.ClassSummary("classname", methods=2, private=1)
        assert str(cls) == "class ``classname'' with 1 public method"


    def test_baseclasses(self):
        base = pc.LocalBaseClass("Local")
        imported = pc.ImportedBaseClass("ImportedClass")
        assert str(base) == "local ``Local''"
        assert str(imported) == "imported ``ImportedClass''"

    def test_inherited_class_summary(self):
        local = pc.ClassSummary("classname", methods=0, private=0,
                                baseclasses=[pc.LocalBaseClass("LocalClass")])
        imported = pc.ClassSummary("classname", methods=0, private=0,
                                   baseclasses=[pc.ImportedBaseClass("ImportedClass")])
        assert str(local) == "class ``classname'' derived from local ``LocalClass'' with 0 public methods" # pylint: disable=line-too-long
        assert str(imported) == "class ``classname'' derived from imported ``ImportedClass'' with 0 public methods" # pylint: disable=line-too-long

    def test_multiple_inherited_summary(self):
        local = pc.ClassSummary("classname", methods=0, private=0,
                                baseclasses=[pc.LocalBaseClass("C1"), pc.LocalBaseClass("C2")])
        with raises(Exception):
            str(local)

class TestClassesExtractor():

    @fixture
    def extractor(self):
        return pc.ClassesExtractor()

    def test_extract_single_class(self, extractor):
        cls = ast.parse("class Klass:\n"
                        "    pass")
        extractor.visit(cls)
        assert extractor.classnames == {"Klass"}
        assert len(extractor.classes) == 1
        summary, = extractor.classes
        assert str(summary) == "class ``Klass'' with 0 public methods"

    def test_extract_multiple_classes(self, extractor):
        cls = ast.parse("class Klass:\n"
                        "    pass\n"
                        "class AnotherKlass:\n"
                        "    pass")
        extractor.visit(cls)
        assert extractor.classnames == {"Klass", "AnotherKlass"}
        assert len(extractor.classes) == 2

    def test_extract_class_with_methods(self, extractor):
        cls = ast.parse("class Klass:\n"
                        "    def __init__(self):\n"
                        "        pass\n"
                        "    def _private_method(self):\n"
                        "        pass\n"
                        "    def public_method(self):\n"
                        "        pass")
        extractor.visit(cls)
        assert len(extractor.classes) == 1
        summary, = extractor.classes
        assert summary.methods == 3
        assert summary.private_methods == 2
        assert summary.public_methods == 1
        assert str(summary) == "class ``Klass'' with 1 public method"

    def test_extract_local_baseclass(self):
        code = ("import os\n"
                "class BaseKlass:\n"
                "    pass\n"
                "class Klass(BaseKlass):\n"
                "    pass\n")
        names = parse_imports(code)
        extractor = pc.ClassesExtractor(names)
        extractor.visit(ast.parse(code))
        assert len(extractor.classes) == 2
        summary, = {cls for cls in extractor.classes if cls.name == "Klass"}
        assert (str(summary) ==
                "class ``Klass'' derived from local ``BaseKlass'' with 0 public methods")

    def test_extract_external_baseclass(self):
        code = ("from module import BaseKlass\n"
                "class Klass(BaseKlass):\n"
                "    pass")
        names = parse_imports(code)
        extractor = pc.ClassesExtractor(names)
        extractor.visit(ast.parse(code))
        assert len(extractor.classes) == 1
        summary, = extractor.classes
        assert (str(summary) ==
                "class ``Klass'' derived from imported ``BaseKlass'' with 0 public methods")

class TestClassesPyfference:
    def test_new_classes(self):
        cpyff = pc.ClassesPyfference(new={"NewClass2", "NewClass"})
        assert cpyff.new == {"NewClass", "NewClass2"}
        assert str(cpyff) == ("New NewClass\n"
                              "New NewClass2")

    def test_simplify(self):
        change = pc.ClassesPyfference(new=set())
        assert change.simplify() is None

class TestPyffClasses:
    def test_new_classes(self):
        old = ("class Klass:\n"
               "    pass")
        new = ("class Klass:\n"
               "    pass\n"
               "class NewKlass:\n"
               "    pass")
        change = pc.pyff_classes(ast.parse(old), ast.parse(new))
        assert change is not None
        assert len(change.new) == 1
        newcls, = change.new
        assert newcls.name == "NewKlass"

    def test_same(self):
        cls = ("class Klass:\n"
               "    pass")
        change = pc.pyff_classes(ast.parse(cls), ast.parse(cls))
        assert change is None
