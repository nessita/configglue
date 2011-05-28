# -*- coding: utf-8 -*-
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

import unittest
import sys
from StringIO import StringIO

from mock import patch, Mock

from configglue.pyschema.glue import (
    configglue,
    schemaconfigglue,
)
from configglue.pyschema.parser import SchemaConfigParser
from configglue.pyschema.schema import (
    ConfigOption,
    ConfigSection,
    IntConfigOption,
    Schema,
    StringConfigOption,
)


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
        class sec1(ConfigSection):
            foo = IntConfigOption()

        sec1 = sec1()
        self.assertTrue(sec1.has_option('foo'))
        self.assertFalse(sec1.has_option('bar'))


class TestSchemaConfigGlue(unittest.TestCase):
    def setUp(self):
        class MySchema(Schema):
            class foo(ConfigSection):
                bar = IntConfigOption()

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
            class foo(ConfigSection):
                baz = IntConfigOption()

            class bar(ConfigSection):
                baz = IntConfigOption()

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

    def test_parser_set_with_encoding(self):
        class MySchema(Schema):
            foo = StringConfigOption()

        parser = SchemaConfigParser(MySchema())
        op, options, args = schemaconfigglue(
            parser, argv=['--foo', 'fóobâr'])
        self.assertEqual(parser.get('__main__', 'foo', parse=False),
            'fóobâr')
        self.assertEqual(parser.get('__main__', 'foo'), 'fóobâr')


class ConfigglueTestCase(unittest.TestCase):
    @patch('configglue.pyschema.glue.SchemaConfigParser')
    @patch('configglue.pyschema.glue.schemaconfigglue')
    def test_configglue_no_errors(self, mock_schemaconfigglue, mock_schema_parser):
        # prepare mocks
        expected_schema_parser = Mock()
        expected_schema_parser.is_valid.return_value = (True, None)
        expected_option_parser = Mock()
        expected_options = Mock()
        expected_args = Mock()
        mock_schemaconfigglue.return_value = (expected_option_parser,
            expected_options, expected_args)
        mock_schema_parser.return_value = expected_schema_parser

        # define the inputs
        class MySchema(Schema):
            foo = IntConfigOption()

        configs = ['config.ini']

        # call the function under test
        glue = configglue(MySchema, configs)

        # schema_parse is a SchemaConfigParser, initialized with MySchema
        # and fed with the configs file list
        self.assertEqual(glue.schema_parser, expected_schema_parser)
        mock_schema_parser.assert_called_with(MySchema())
        mock_schema_parser.return_value.read.assert_called_with(configs)
        # the other attributes are the result of calling schemaconfigglue
        mock_schemaconfigglue.assert_called_with(expected_schema_parser, op=None)
        self.assertEqual(glue.option_parser, expected_option_parser)
        self.assertEqual(glue.options, expected_options)
        self.assertEqual(glue.args, expected_args)

    @patch('configglue.pyschema.glue.SchemaConfigParser')
    @patch('configglue.pyschema.glue.schemaconfigglue')
    def test_configglue_with_errors(self, mock_schemaconfigglue, mock_schema_parser):
        # prepare mocks
        expected_schema_parser = Mock()
        expected_schema_parser.is_valid.return_value = (False, ['some error'])
        expected_option_parser = Mock()
        expected_options = Mock()
        expected_args = Mock()
        mock_schemaconfigglue.return_value = (expected_option_parser,
            expected_options, expected_args)
        mock_schema_parser.return_value = expected_schema_parser

        # define the inputs
        class MySchema(Schema):
            foo = IntConfigOption()

        configs = ['config.ini']

        # call the function under test
        glue = configglue(MySchema, configs)

        # schema_parse is a SchemaConfigParser, initialized with MySchema
        # and fed with the configs file list
        self.assertEqual(glue.schema_parser, expected_schema_parser)
        mock_schema_parser.assert_called_with(MySchema())
        mock_schema_parser.return_value.read.assert_called_with(configs)
        # the other attributes are the result of calling schemaconfigglue
        mock_schemaconfigglue.assert_called_with(expected_schema_parser, op=None)
        self.assertEqual(glue.option_parser, expected_option_parser)
        expected_option_parser.error.assert_called_with('some error')
        self.assertEqual(glue.options, expected_options)
        self.assertEqual(glue.args, expected_args)

    @patch('configglue.pyschema.glue.OptionParser')
    @patch('configglue.pyschema.glue.SchemaConfigParser')
    @patch('configglue.pyschema.glue.schemaconfigglue')
    def test_configglue_with_usage(self, mock_schemaconfigglue,
        mock_schema_parser, mock_option_parser):
        # prepare mocks
        expected_schema_parser = Mock()
        expected_schema_parser.is_valid.return_value = (True, None)
        expected_option_parser = mock_option_parser.return_value
        expected_options = Mock()
        expected_args = Mock()
        mock_schemaconfigglue.return_value = (expected_option_parser, expected_options,
            expected_args)
        mock_schema_parser.return_value = expected_schema_parser

        # define the inputs
        class MySchema(Schema):
            foo = IntConfigOption()

        configs = ['config.ini']

        # call the function under test
        glue = configglue(MySchema, configs, usage='foo')

        # schema_parse is a SchemaConfigParser, initialized with MySchema
        # and fed with the configs file list
        self.assertEqual(glue.schema_parser, expected_schema_parser)
        mock_schema_parser.assert_called_with(MySchema())
        mock_schema_parser.return_value.read.assert_called_with(configs)
        # the other attributes are the result of calling schemaconfigglue
        mock_schemaconfigglue.assert_called_with(expected_schema_parser,
            op=expected_option_parser)
        mock_option_parser.assert_called_with(usage='foo')
        self.assertEqual(glue.option_parser, expected_option_parser)
        self.assertEqual(glue.options, expected_options)
        self.assertEqual(glue.args, expected_args)

