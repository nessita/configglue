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
import os
import sys
from StringIO import StringIO

from mock import (
    Mock,
    patch,
    patch_object,
)

from configglue.pyschema.glue import (
    configglue,
    schemaconfigglue,
)
from configglue.pyschema.parser import SchemaConfigParser
from configglue.pyschema.schema import (
    Option,
    Section,
    IntOption,
    Schema,
    StringOption,
)


class TestOption(unittest.TestCase):
    def test_repr_name(self):
        opt = Option()
        expected = "<Option>"
        self.assertEqual(repr(opt), expected)

        opt = Option(name='name')
        expected = "<Option name>"
        self.assertEqual(repr(opt), expected)

        sect = Section(name='sect')
        opt = Option(name='name', section=sect)
        expected = "<Option sect.name>"
        self.assertEqual(repr(opt), expected)

    def test_repr_extra(self):
        opt = Option(name='name', raw=True)
        expected = "<Option name raw>"
        self.assertEqual(repr(opt), expected)

        opt = Option(name='name', fatal=True)
        expected = "<Option name fatal>"
        self.assertEqual(repr(opt), expected)

        opt = Option(name='name', raw=True, fatal=True)
        expected = "<Option name raw fatal>"
        self.assertEqual(repr(opt), expected)

    def test_parse(self):
        opt = Option()
        self.assertRaises(NotImplementedError, opt.parse, '')

    def test_equal(self):
        opt1 = Option()
        opt2 = Option(name='name', raw=True)

        self.assertEqual(opt1, Option())
        self.assertEqual(opt2, Option(name='name', raw=True))
        self.assertNotEqual(opt1, opt2)
        self.assertNotEqual(opt1, None)


class TestSection(unittest.TestCase):
    def test_repr_name(self):
        sect = Section()
        expected = "<Section>"
        self.assertEqual(repr(sect), expected)

        sect = Section(name='sect')
        expected = "<Section sect>"
        self.assertEqual(repr(sect), expected)

    def test_equal(self):
        sec1 = Section()
        sec2 = Section(name='sec2')

        self.assertEqual(sec1, Section())
        self.assertEqual(sec2, Section(name='sec2'))
        self.assertNotEqual(sec1, sec2)

    def test_has_option(self):
        class sec1(Section):
            foo = IntOption()

        sec1 = sec1()
        self.assertTrue(sec1.has_option('foo'))
        self.assertFalse(sec1.has_option('bar'))


class TestSchemaConfigGlue(unittest.TestCase):
    def setUp(self):
        class MySchema(Schema):
            class foo(Section):
                bar = IntOption()

            baz = IntOption(help='The baz option')

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

        _argv, sys.argv = sys.argv, []
        try:
            op, options, args = schemaconfigglue(self.parser)
            self.assertEqual(self.parser.values(),
                {'foo': {'bar': 0}, '__main__': {'baz': 1}})
        finally:
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

    @patch('configglue.pyschema.glue.os')
    def test_glue_environ(self, mock_os):
        mock_os.environ = {'CONFIGGLUE_FOO_BAR': '42', 'CONFIGGLUE_BAZ': 3}
        config = StringIO("[foo]\nbar=1")
        self.parser.readfp(config)

        _argv, sys.argv = sys.argv, ['prognam']
        try:
            op, options, args = schemaconfigglue(self.parser)
            self.assertEqual(self.parser.values(),
                {'foo': {'bar': 42}, '__main__': {'baz': 3}})
        finally:
            sys.argv = _argv


    def test_glue_environ_precedence(self):
        with patch_object(os, 'environ',
            {'CONFIGGLUE_FOO_BAR': '42', 'BAR': '1'}):

            config = StringIO("[foo]\nbar=$BAR")
            self.parser.readfp(config)

            _argv, sys.argv = sys.argv, ['prognam']
            try:
                op, options, args = schemaconfigglue(self.parser)
                self.assertEqual(self.parser.get('foo', 'bar'), 42)
            finally:
                sys.argv = _argv

    def test_ambiguous_option(self):
        class MySchema(Schema):
            class foo(Section):
                baz = IntOption()

            class bar(Section):
                baz = IntOption()

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
            foo = StringOption()

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
            foo = IntOption()

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
            foo = IntOption()

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
            foo = IntOption()

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

