# pylint: disable=missing-docstring, no-self-use, too-few-public-methods

import ast
from typing import Tuple
from pytest import raises, fixture
import pyff.classes as pc
import pyff.imports as pi
import pyff.functions as pf
from helpers import parse_imports


class TestPyffClass:
    @staticmethod
    def _make_summary(classname: str, code: str) -> Tuple[pc.ClassSummary, pi.ImportedNames]:
        import_walker = pi.ImportExtractor()
        code_ast = ast.parse(code)
        import_walker.visit(code_ast)
        walker = pc.ClassesExtractor(import_walker.names)
        walker.visit(code_ast)
        return (walker.classes[classname], import_walker.names)

    def test_new_method(self):
        old, old_imports = self._make_summary("Klass", "class Klass:\n    pass")
        new, new_imports = self._make_summary(
            "Klass", "class Klass:\n    def __init__(self):        pass"
        )

        change = pc.pyff_class(old, new, old_imports, new_imports)
        assert change is not None
        assert change.methods
        assert "__init__" in change.methods.new


class TestClassPyfference:
    def test_methods(self):
        old = ast.parse("")
        new = ast.parse("def method():\n    pass")
        methods = pf.pyff_functions(
            old, new, pi.ImportedNames.extract(old), pi.ImportedNames.extract(new)
        )
        change = pc.ClassPyfference(name="Klass", methods=methods, attributes=None)
        assert change.methods is not None
        assert change.attributes is None
        assert "method" in change.methods.new
        assert str(change) == "Class ``Klass'' changed:\n  New method ``method''"

    def test_attributes(self):
        change = pc.ClassPyfference(
            name="Klasse",
            methods=None,
            attributes=pc.AttributesPyfference(removed=None, new={"super"}),
        )
        assert change.methods is None
        assert change.attributes is not None
        assert change.attributes.new == {"super"}
        assert str(change) == "Class ``Klasse'' changed:\n  New attribute ``super''"


class TestClassSummary:
    @fixture
    def classdef(self):
        return ast.ClassDef(name="Klass", bases=[], keywords=[], body=[], decorator_list=[])

    def test_class_summary(self, classdef):
        cls = pc.ClassSummary(
            methods={"a", "b", "c", "_d", "_e"}, definition=classdef, attributes=set()
        )
        assert cls.name == "Klass"
        assert cls.methods == {"a", "b", "c", "_d", "_e"}
        assert cls.private_methods == {"_d", "_e"}
        assert cls.public_methods == {"a", "b", "c"}
        assert str(cls) == "class ``Klass'' with 3 public methods"

        another_def = self.classdef()
        another_def.name = "Llass"
        another = pc.ClassSummary(methods=set(), attributes={}, definition=another_def)
        assert cls < another
        another_def.name = "Jlass"
        assert cls > another

    def test_attributes(self, classdef):
        cls = pc.ClassSummary(
            methods={"__init__"}, definition=classdef, attributes={"attrib", "field"}
        )
        assert cls.attributes == {"attrib", "field"}

    def test_singular(self, classdef):
        cls = pc.ClassSummary(methods={"__init__", "a"}, definition=classdef, attributes=set())
        assert str(cls) == "class ``Klass'' with 1 public method"

    def test_baseclasses(self):
        base = pc.LocalBaseClass("Local")
        imported = pc.ImportedBaseClass("ImportedClass")
        assert str(base) == "local ``Local''"
        assert str(imported) == "imported ``ImportedClass''"

    def test_inherited_class_summary(self, classdef):
        local = pc.ClassSummary(
            methods=set(),
            baseclasses=[pc.LocalBaseClass("LocalClass")],
            definition=classdef,
            attributes=set(),
        )
        imported = pc.ClassSummary(
            methods=set(),
            baseclasses=[pc.ImportedBaseClass("ImportedClass")],
            definition=classdef,
            attributes=set(),
        )
        assert (
            str(local) == "class ``Klass'' derived from local ``LocalClass'' with 0 public methods"
        )  # pylint: disable=line-too-long
        assert (
            str(imported)
            == "class ``Klass'' derived from imported ``ImportedClass'' with 0 public methods"
        )  # pylint: disable=line-too-long

    def test_multiple_inherited_summary(self, classdef):
        local = pc.ClassSummary(
            methods=set(),
            baseclasses=[pc.LocalBaseClass("C1"), pc.LocalBaseClass("C2")],
            definition=classdef,
            attributes=set(),
        )
        with raises(Exception):
            str(local)


class TestAttributesPyfference:
    def test_sanity(self):
        change = pc.AttributesPyfference(removed={"gone"}, new={"super", "duper"})
        assert change
        assert change.new == {"super", "duper"}
        assert change.removed == {"gone"}
        assert str(change) == "Removed attribute ``gone''\nNew attributes ``duper'', ``super''"

    def test_empty(self):
        change = pc.AttributesPyfference(removed=set(), new=set())
        assert not change


class TestClassesExtractor:
    @fixture
    def extractor(self):
        return pc.ClassesExtractor()

    def test_extract_single_class(self, extractor):
        cls = ast.parse("class Klass:\n" "    pass")
        extractor.visit(cls)
        assert extractor.classnames == {"Klass"}
        assert len(extractor.classes) == 1
        assert "Klass" in extractor.classes
        summary = extractor.classes["Klass"]
        assert str(summary) == "class ``Klass'' with 0 public methods"

    def test_extract_multiple_classes(self, extractor):
        cls = ast.parse("class Klass:\n" "    pass\n" "class AnotherKlass:\n" "    pass")
        extractor.visit(cls)
        assert extractor.classnames == {"Klass", "AnotherKlass"}
        assert len(extractor.classes) == 2

    def test_extract_class_with_methods(self, extractor):
        cls = ast.parse(
            "class Klass:\n"
            "    def __init__(self):\n"
            "        pass\n"
            "    def _private_method(self):\n"
            "        pass\n"
            "    def public_method(self):\n"
            "        pass"
        )
        extractor.visit(cls)
        assert len(extractor.classes) == 1
        summary = extractor.classes["Klass"]
        assert summary.methods == {"__init__", "_private_method", "public_method"}
        assert summary.private_methods == {"__init__", "_private_method"}
        assert summary.public_methods == {"public_method"}
        assert str(summary) == "class ``Klass'' with 1 public method"

    def test_extract_local_baseclass(self):
        code = (
            "import os\n" "class BaseKlass:\n" "    pass\n" "class Klass(BaseKlass):\n" "    pass\n"
        )
        names = parse_imports(code)
        extractor = pc.ClassesExtractor(names)
        extractor.visit(ast.parse(code))
        assert len(extractor.classes) == 2
        summary = extractor.classes["Klass"]
        assert (
            str(summary) == "class ``Klass'' derived from local ``BaseKlass'' with 0 public methods"
        )

    def test_extract_external_baseclass(self):
        code = "from module import BaseKlass\n" "class Klass(BaseKlass):\n" "    pass"
        names = parse_imports(code)
        extractor = pc.ClassesExtractor(names)
        extractor.visit(ast.parse(code))
        assert len(extractor.classes) == 1
        summary = extractor.classes["Klass"]
        assert (
            str(summary)
            == "class ``Klass'' derived from imported ``BaseKlass'' with 0 public methods"
        )

    def test_extract_attribute(self, extractor):
        klass = ast.parse("class Klass:\n  def __init__(self, value):\n    self.attribute = value")
        extractor.visit(klass)
        summary = extractor.classes["Klass"]
        assert summary.attributes == {"attribute"}

    def test_extract_annotated_attribute(self, extractor):  # pylint: disable=invalid-name
        klass = ast.parse(
            "class Klass:\n  def __init__(self, value):\n    self.attribute: typehint = value"
        )
        extractor.visit(klass)
        summary = extractor.classes["Klass"]
        assert summary.attributes == {"attribute"}


class TestClassesPyfference:
    def test_new_classes(self):
        cpyff = pc.ClassesPyfference(new={"NewClass2", "NewClass"}, changed=set())
        assert cpyff.new == {"NewClass", "NewClass2"}
        assert str(cpyff) == ("New NewClass\n" "New NewClass2")

    def test_simplify(self):
        change = pc.ClassesPyfference(new=set(), changed=set())
        assert change.simplify() is None


class TestPyffClasses:
    def test_new_classes(self):
        old = ast.parse("class Klass:\n" "    pass")
        new = ast.parse("class Klass:\n" "    pass\n" "class NewKlass:\n" "    pass")
        old_imports = pi.ImportedNames.extract(old)
        new_imports = pi.ImportedNames.extract(new)
        change = pc.pyff_classes(old, new, old_imports, new_imports)
        assert change is not None
        assert len(change.new) == 1
        newcls, = change.new
        assert newcls.name == "NewKlass"

    def test_same(self):
        cls = "class Klass:\n" "    pass"
        imports = pi.ImportedNames.extract(ast.parse(cls))
        change = pc.pyff_classes(ast.parse(cls), ast.parse(cls), imports, imports)
        assert change is None

    def test_changed_class(self):
        old = ast.parse("class Klass:\n    pass")
        new = ast.parse("class Klass:\n    def __init__(self):\n        pass")
        old_imports = pi.ImportedNames.extract(old)
        new_imports = pi.ImportedNames.extract(new)
        change = pc.pyff_classes(old, new, old_imports, new_imports)
        assert change is not None
        assert "Klass" in change.changed
