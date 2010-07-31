###############################################################################
# 
# configglue -- glue for your apps' configuration
# 
# A library for simple, DRY configuration of applications
# 
# (C) 2009--2010 by Canonical Ltd.
# originally by John R. Lenton <john.lenton@canonical.com>
# incorporating schemaconfig as configglue.pyschema
# schemaconfig originally by Ricardo Kirkner <ricardo.kirkner@canonical.com>
# 
# Released under the BSD License (see the file LICENSE)
# 
# For bug reports, support, and new releases: http://launchpad.net/configglue
# 
###############################################################################

# Copyright 2010 Canonical Ltd.  This software is licensed under the
# GNU Lesser General Public License version 3 (see the file LICENSE).

import unittest
from StringIO import StringIO

from configglue.pyschema import ConfigSection
from configglue.pyschema.options import (BoolConfigOption, DictConfigOption,
    IntConfigOption, StringConfigOption, LinesConfigOption)
from configglue.pyschema.schema import Schema


class TestSchema(unittest.TestCase):
    def test_sections(self):
        class MySchema(Schema):
            foo = BoolConfigOption()

        class MyOtherSchema(Schema):
            web = ConfigSection()
            web.bar = IntConfigOption()
            froo = ConfigSection()
            froo.twaddle = LinesConfigOption(item=BoolConfigOption())

        class MyThirdSchema(Schema):
            bar = IntConfigOption()
            froo = ConfigSection()
            froo.twaddle = LinesConfigOption(item=BoolConfigOption())

        schema = MySchema()
        names = set(s.name for s in schema.sections())
        self.assertEquals(set(['__main__']), names)

        schema = MyOtherSchema()
        names = set(s.name for s in schema.sections())
        self.assertEquals(set(['web', 'froo']), names)

        schema = MyThirdSchema()
        names = set(s.name for s in schema.sections())
        self.assertEquals(set(['__main__', 'froo']), names)

    def test_schema_validation(self):
        class BorkenSchema(Schema):
            __main__ = ConfigSection()
            __main__.foo = BoolConfigOption()

        class SomeSchema(Schema):
            mysection = ConfigSection()

        schema = BorkenSchema()
        self.assertFalse(schema.is_valid())

        schema = SomeSchema()
        self.assertTrue(schema.is_valid())

    def test_names(self):
        class MySchema(Schema):
            foo = BoolConfigOption()
            bar = ConfigSection()
            bar.baz = IntConfigOption()

        schema = MySchema()
        self.assertEquals('foo', schema.foo.name)
        self.assertEquals('__main__', schema.foo.section.name)
        self.assertEquals('bar', schema.bar.name)
        self.assertEquals('baz', schema.bar.baz.name)
        self.assertEquals('bar', schema.bar.baz.section.name)

    def test_options(self):
        class MySchema(Schema):
            foo = BoolConfigOption()
            bar = ConfigSection()
            bar.baz = IntConfigOption()

        schema = MySchema()
        names = set(s.name for s in schema.options())
        self.assertEquals(set(['foo', 'baz']), names)
        names = set(s.name for s in schema.options('__main__'))
        self.assertEquals(set(['foo']), names)
        names = set(s.name for s in schema.options('bar'))
        self.assertEquals(set(['baz']), names)

    def test_include(self):
        schema = Schema()
        self.assertTrue(hasattr(schema, 'includes'))

    def test_equal(self):
        class MySchema(Schema):
            foo = IntConfigOption()
        class OtherSchema(Schema):
            bar = IntConfigOption()

        self.assertEqual(MySchema(), MySchema())
        self.assertNotEqual(MySchema(), OtherSchema())


class TestSchemaInheritance(unittest.TestCase):
    def setUp(self):
        class SchemaA(Schema):
            foo = ConfigSection()
            foo.bar = IntConfigOption()
        class SchemaB(SchemaA):
            baz = ConfigSection()
            baz.wham = IntConfigOption()

        self.schema = SchemaB()

    def test_basic_inheritance(self):
        names = [('foo', ['bar']), ('baz', ['wham'])]
        for section, options in names:
            section_obj = getattr(self.schema, section)
            self.assertTrue(isinstance(section_obj, ConfigSection))
            for option in options:
                option_obj = getattr(section_obj, option)
                self.assertTrue(isinstance(option_obj, IntConfigOption))

    def test_inherited_sections(self):
        names = set(s.name for s in self.schema.sections())
        self.assertEqual(set(['foo', 'baz']), names)

    def test_inherited_options(self):
        names = set(s.name for s in self.schema.options())
        self.assertEqual(set(['bar', 'wham']), names)

