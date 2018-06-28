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
        change = pc.ClassPyfference(methods=methods)
        assert change.methods is not None
        assert "method" in change.methods.new


class TestClassSummary:
    @fixture
    def classdef(self):
        return ast.ClassDef(name="Klass", bases=[], keywords=[], body=[], decorator_list=[])

    def test_class_summary(self, classdef):
        cls = pc.ClassSummary(methods=5, private=2, definition=classdef)
        assert cls.name == "Klass"
        assert cls.methods == 5
        assert cls.private_methods == 2
        assert cls.public_methods == 3
        assert str(cls) == "class ``Klass'' with 3 public methods"

    def test_singular(self, classdef):
        cls = pc.ClassSummary(methods=2, private=1, definition=classdef)
        assert str(cls) == "class ``Klass'' with 1 public method"

    def test_baseclasses(self):
        base = pc.LocalBaseClass("Local")
        imported = pc.ImportedBaseClass("ImportedClass")
        assert str(base) == "local ``Local''"
        assert str(imported) == "imported ``ImportedClass''"

    def test_inherited_class_summary(self, classdef):
        local = pc.ClassSummary(
            methods=0, private=0, baseclasses=[pc.LocalBaseClass("LocalClass")], definition=classdef
        )
        imported = pc.ClassSummary(
            methods=0,
            private=0,
            baseclasses=[pc.ImportedBaseClass("ImportedClass")],
            definition=classdef,
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
            methods=0,
            private=0,
            baseclasses=[pc.LocalBaseClass("C1"), pc.LocalBaseClass("C2")],
            definition=classdef,
        )
        with raises(Exception):
            str(local)


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
        assert summary.methods == 3
        assert summary.private_methods == 2
        assert summary.public_methods == 1
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
