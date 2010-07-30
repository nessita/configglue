# Copyright 2010 Canonical Ltd.  This software is licensed under the
# GNU Lesser General Public License version 3 (see the file LICENSE).

import unittest
import sys
from StringIO import StringIO

from configglue.pyschema import ConfigOption, ConfigSection, schemaconfigglue
from configglue.pyschema.options import IntConfigOption
from configglue.pyschema.parser import SchemaConfigParser
from configglue.pyschema.schema import Schema


class TestConfigOption(unittest.TestCase):
    def test_repr_name(self):
        opt = ConfigOption()
        expected = "<ConfigOption>"
        self.assertEqual(repr(opt), expected)

        opt = ConfigOption(name='name')
        expected = "<ConfigOption name>"
        self.assertEqual(repr(opt), expected)

        sect = ConfigSection(name='sect')
        opt = ConfigOption(name='name', section=sect)
        expected = "<ConfigOption sect.name>"
        self.assertEqual(repr(opt), expected)

    def test_repr_extra(self):
        opt = ConfigOption(name='name', raw=True)
        expected = "<ConfigOption name raw>"
        self.assertEqual(repr(opt), expected)

        opt = ConfigOption(name='name', fatal=True)
        expected = "<ConfigOption name fatal>"
        self.assertEqual(repr(opt), expected)

        opt = ConfigOption(name='name', raw=True, fatal=True)
        expected = "<ConfigOption name raw fatal>"
        self.assertEqual(repr(opt), expected)

    def test_parse(self):
        opt = ConfigOption()
        self.assertRaises(NotImplementedError, opt.parse, '')

    def test_equal(self):
        opt1 = ConfigOption()
        opt2 = ConfigOption(name='name', raw=True)

        self.assertEqual(opt1, ConfigOption())
        self.assertEqual(opt2, ConfigOption(name='name', raw=True))
        self.assertNotEqual(opt1, opt2)
        self.assertNotEqual(opt1, None)


class TestConfigSection(unittest.TestCase):
    def test_repr_name(self):
        sect = ConfigSection()
        expected = "<ConfigSection>"
        self.assertEqual(repr(sect), expected)

        sect = ConfigSection(name='sect')
        expected = "<ConfigSection sect>"
        self.assertEqual(repr(sect), expected)

    def test_equal(self):
        sec1 = ConfigSection()
        sec2 = ConfigSection(name='sec2')

        self.assertEqual(sec1, ConfigSection())
        self.assertEqual(sec2, ConfigSection(name='sec2'))
        self.assertNotEqual(sec1, sec2)

    def test_has_option(self):
        sec1 = ConfigSection()
        sec1.foo = IntConfigOption()

        self.assertTrue(sec1.has_option('foo'))
        self.assertFalse(sec1.has_option('bar'))


class TestSchemaConfigGlue(unittest.TestCase):
    def setUp(self):
        class MySchema(Schema):
            foo = ConfigSection()
            foo.bar = IntConfigOption()

            baz = IntConfigOption(help='The baz option')

        self.parser = SchemaConfigParser(MySchema())

    def test_glue_no_op(self):
        config = StringIO("[__main__]\nbaz=1")
        self.parser.readfp(config)
        self.assertEqual(self.parser.values(),
            {'foo': {'bar': 0}, '__main__': {'baz': 1}})

        op, options, args = schemaconfigglue(self.parser, argv=['--baz', '2'])
        self.assertEqual(self.parser.values(),
            {'foo': {'bar': 0}, '__main__': {'baz': 2}})

    def test_glue_no_argv(self):
        config = StringIO("[__main__]\nbaz=1")
        self.parser.readfp(config)
        self.assertEqual(self.parser.values(),
            {'foo': {'bar': 0}, '__main__': {'baz': 1}})

        _argv = sys.argv
        sys.argv = []

        op, options, args = schemaconfigglue(self.parser)
        self.assertEqual(self.parser.values(),
            {'foo': {'bar': 0}, '__main__': {'baz': 1}})

        sys.argv = _argv

    def test_glue_section_option(self):
        config = StringIO("[foo]\nbar=1")
        self.parser.readfp(config)
        self.assertEqual(self.parser.values(),
            {'foo': {'bar': 1}, '__main__': {'baz': 0}})

        op, options, args = schemaconfigglue(self.parser,
                                             argv=['--foo_bar', '2'])
        self.assertEqual(self.parser.values(),
                         {'foo': {'bar': 2}, '__main__': {'baz': 0}})

    def test_ambiguous_option(self):
        class MySchema(Schema):
            foo = ConfigSection()
            foo.baz = IntConfigOption()

            bar = ConfigSection()
            bar.baz = IntConfigOption()

        config = StringIO("[foo]\nbaz=1")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertEqual(parser.values('foo'), {'baz': 1})
        self.assertEqual(parser.values('bar'), {'baz': 0})

        op, options, args = schemaconfigglue(
            parser, argv=['--bar_baz', '2'])
        self.assertEqual(parser.values('foo'), {'baz': 1})
        self.assertEqual(parser.values('bar'), {'baz': 2})

    def test_help(self):
        config = StringIO("[foo]\nbar=1")
        self.parser.readfp(config)
        self.assertEqual(self.parser.values(),
            {'foo': {'bar': 1}, '__main__': {'baz': 0}})

        # replace stdout to capture its value
        stdout = StringIO()
        _stdout = sys.stdout
        sys.stdout = stdout
        # call the method and assert its value
        self.assertRaises(SystemExit, schemaconfigglue, self.parser,
            argv=['--help'])
        # replace stdout again to cleanup
        sys.stdout = _stdout

        # assert the value of stdout is correct
        stdout.seek(0)
        output = stdout.read()
        self.assertTrue(output.startswith('Usage:'))

