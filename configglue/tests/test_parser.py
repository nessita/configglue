# -*- coding: utf-8 -*-
###############################################################################
#
# configglue -- glue for your apps' configuration
#
# A library for simple, DRY configuration of applications
#
# (C) 2009--2011 by Canonical Ltd.
# by John R. Lenton <john.lenton@canonical.com>
# and Ricardo Kirkner <ricardo.kirkner@canonical.com>
#
# Released under the BSD License (see the file LICENSE)
#
# For bug reports, support, and new releases: http://launchpad.net/configglue
#
###############################################################################

import logging
import os
import shutil
import tempfile
import textwrap
import unittest
from ConfigParser import (
    DEFAULTSECT,
    InterpolationDepthError,
    InterpolationMissingOptionError,
    InterpolationSyntaxError,
    NoSectionError,
)
from StringIO import StringIO

from mock import (
    Mock,
    patch,
)

from configglue.parser import (
    CONFIG_FILE_ENCODING,
    NoOptionError,
    SchemaConfigParser,
    SchemaValidationError,
)
from configglue.schema import (
    BoolOption,
    Section,
    DictOption,
    IntOption,
    ListOption,
    Schema,
    StringOption,
    TupleOption,
)


# backwards compatibility
if not hasattr(patch, 'object'):
    # mock < 0.8
    from mock import patch_object
    patch.object = patch_object


class TestIncludes(unittest.TestCase):
    def setUp(self):
        class MySchema(Schema):
            foo = StringOption()
        self.schema = MySchema()
        fd, self.name = tempfile.mkstemp(suffix='.cfg')
        os.write(fd, '[__main__]\nfoo=bar\n')
        os.close(fd)

        # disable logging output during test
        self.level = logging.getLogger().level
        logging.disable('ERROR')

    def tearDown(self):
        os.remove(self.name)

        # re-enable original logging level
        logging.getLogger().setLevel(self.level)

    def test_basic_include(self):
        config = StringIO('[__main__]\nincludes=%s' % self.name)
        parser = SchemaConfigParser(self.schema)
        parser.readfp(config, 'my.cfg')
        self.assertEquals({'__main__': {'foo': 'bar'}}, parser.values())

    def test_locate(self):
        config = StringIO("[__main__]\nincludes=%s" % self.name)
        parser = SchemaConfigParser(self.schema)
        parser.readfp(config, 'my.cfg')

        location = parser.locate(option='foo')
        expected_location = self.name
        self.assertEqual(expected_location, location)

    @patch('configglue.parser.logging.warn')
    @patch('configglue.parser.codecs.open')
    def test_read_ioerror(self, mock_open, mock_warn):
        mock_open.side_effect = IOError

        parser = SchemaConfigParser(self.schema)
        read_ok = parser.read(self.name)

        self.assertEqual(read_ok, [])
        self.assertEqual(mock_warn.call_args_list,
            [(("File {0} could not be read. Skipping.".format(self.name),),
              {})])

    def test_relative_include(self):
        """Test parser include files using relative paths."""
        def setup_config():
            folder = tempfile.mkdtemp()

            f = open("%s/first.cfg" % folder, 'w')
            f.write("[__main__]\nfoo=1\nincludes=second.cfg")
            f.close()

            f = open("%s/second.cfg" % folder, 'w')
            f.write("[__main__]\nbar=2\nincludes=sub/third.cfg")
            f.close()

            os.mkdir("%s/sub" % folder)
            f = open("%s/sub/third.cfg" % folder, 'w')
            f.write("[__main__]\nincludes=../fourth.cfg")
            f.close()

            f = open("%s/fourth.cfg" % folder, 'w')
            f.write("[__main__]\nbaz=3")
            f.close()

            config = StringIO("[__main__]\nincludes=%s/first.cfg" % folder)
            return config, folder

        class MySchema(Schema):
            foo = IntOption()
            bar = IntOption()
            baz = IntOption()

        config, folder = setup_config()
        expected_values = {'__main__': {'foo': 1, 'bar': 2, 'baz': 3}}
        parser = SchemaConfigParser(MySchema())
        # make sure we start on a clean basedir
        self.assertEqual(parser._basedir, '')
        parser.readfp(config, 'my.cfg')
        self.assertEqual(parser.values(), expected_values)
        # make sure we leave the basedir clean
        self.assertEqual(parser._basedir, '')

        # silently remove any created files
        try:
            shutil.rmtree(folder)
        except:
            pass

    def test_local_override(self):
        """Test parser override values from included files."""
        def setup_config():
            folder = tempfile.mkdtemp()

            f = open("%s/first.cfg" % folder, 'w')
            f.write("[__main__]\nfoo=1\nbar=2\nincludes=second.cfg")
            f.close()

            f = open("%s/second.cfg" % folder, 'w')
            f.write("[__main__]\nbaz=3")
            f.close()

            config = StringIO(
                "[__main__]\nfoo=4\nincludes=%s/first.cfg" % folder)
            return config, folder

        class MySchema(Schema):
            foo = IntOption()
            bar = IntOption()
            baz = IntOption()

        config, folder = setup_config()
        expected_values = {'__main__': {'foo': 4, 'bar': 2, 'baz': 3}}
        parser = SchemaConfigParser(MySchema())
        # make sure we start on a clean basedir
        self.assertEqual(parser._basedir, '')
        parser.readfp(config, 'my.cfg')
        self.assertEqual(parser.values(), expected_values)
        # make sure we leave the basedir clean
        self.assertEqual(parser._basedir, '')

        # silently remove any created files
        try:
            shutil.rmtree(folder)
        except:
            pass


class TestInterpolation(unittest.TestCase):
    """Test basic interpolation."""
    def test_basic_interpolate(self):
        class MySchema(Schema):
            foo = StringOption()
            bar = BoolOption()
        config = StringIO('[__main__]\nbar=%(foo)s\nfoo=True')
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config, 'my.cfg')
        self.assertEquals({'__main__': {'foo': 'True', 'bar': True}},
                          parser.values())

    def test_interpolate_missing_option(self):
        """Test interpolation with a missing option."""
        class MySchema(Schema):
            foo = StringOption()
            bar = BoolOption()

        section = '__main__'
        option = 'foo'
        rawval = '%(baz)s'
        vars = {}
        parser = SchemaConfigParser(MySchema())
        self.assertRaises(InterpolationMissingOptionError,
            parser._interpolate, section, option, rawval, vars)

    def test_interpolate_too_deep(self):
        """Test too deeply recursive interpolation."""
        class MySchema(Schema):
            foo = StringOption()
            bar = BoolOption()

        section = '__main__'
        option = 'foo'
        rawval = '%(bar)s'
        vars = {'foo': '%(bar)s', 'bar': '%(foo)s'}
        parser = SchemaConfigParser(MySchema())
        self.assertRaises(InterpolationDepthError,
            parser._interpolate, section, option, rawval, vars)

    def test_interpolate_incomplete_format(self):
        """Test interpolation with incomplete format key."""
        class MySchema(Schema):
            foo = StringOption()
            bar = BoolOption()

        section = '__main__'
        option = 'foo'
        rawval = '%(bar)'
        vars = {'foo': '%(bar)s', 'bar': 'pepe'}
        parser = SchemaConfigParser(MySchema())
        self.assertRaises(InterpolationSyntaxError, parser._interpolate,
            section, option, rawval, vars)

    def test_interpolate_across_sections(self):
        """Test interpolation across sections."""
        class MySchema(Schema):
            class foo(Section):
                bar = IntOption()

            class baz(Section):
                wham = IntOption()

        config = StringIO("[foo]\nbar=%(wham)s\n[baz]\nwham=42")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertRaises(InterpolationMissingOptionError,
            parser.get, 'foo', 'bar')

    def test_interpolate_invalid_key(self):
        """Test interpolation of invalid key."""
        class MySchema(Schema):
            class foo(Section):
                bar = IntOption()

            class baz(Section):
                wham = IntOption()

        config = StringIO("[foo]\nbar=%(wham)s\n[baz]\nwham=42")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertRaises(InterpolationMissingOptionError, parser.get,
                          'foo', 'bar')

    @patch('configglue.parser.os')
    def test_interpolate_environment_basic_syntax(self, mock_os):
        mock_os.environ = {'PATH': 'foo'}
        parser = SchemaConfigParser(Schema())
        result = parser.interpolate_environment("$PATH")
        self.assertEqual(result, 'foo')

    @patch('configglue.parser.os')
    def test_interpolate_environment_extended_syntax(self, mock_os):
        mock_os.environ = {'PATH': 'foo'}
        parser = SchemaConfigParser(Schema())
        result = parser.interpolate_environment("${PATH}")
        self.assertEqual(result, 'foo')

    @patch('configglue.parser.os')
    def test_interpolate_environment_in_config(self, mock_os):
        mock_os.environ = {'PYTHONPATH': 'foo', 'PATH': 'bar'}

        class MySchema(Schema):
            pythonpath = StringOption()
            path = StringOption()

        config = StringIO("[__main__]\npythonpath=${PYTHONPATH}\npath=$PATH")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertEqual(parser.values('__main__'),
            {'pythonpath': 'foo', 'path': 'bar'})

    def test_interpolate_environment_without_keys(self):
        parser = SchemaConfigParser(Schema())
        rawval = "['%H:%M:%S', '%Y-%m-%d']"
        value = parser.interpolate_environment(rawval)
        self.assertEqual(value, rawval)

    @patch('configglue.parser.os')
    def test_get_with_environment_var(self, mock_os):
        mock_os.environ = {'FOO': '42'}
        class MySchema(Schema):
            foo = IntOption()

        config = StringIO("[__main__]\nfoo=$FOO")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertEqual(parser.get('__main__', 'foo'), 42)

    def test_get_without_environment_var(self):
        class MySchema(Schema):
            foo = IntOption()

        config = StringIO("[__main__]\nfoo=$FOO")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertEqual(parser.get('__main__', 'foo'), 0)

    def test_get_interpolation_keys_string(self):
        """Test get_interpolation_keys for a string."""
        class MySchema(Schema):
            foo = StringOption()
        config = StringIO("[__main__]\nfoo=%(bar)s")
        expected = ('%(bar)s', set(['bar']))

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        result = parser._get_interpolation_keys('__main__', 'foo')
        self.assertEqual(result, expected)

    def test_get_interpolation_keys_int(self):
        """Test get_interpolation_keys for an integer."""
        class MySchema(Schema):
            foo = IntOption()
        config = StringIO("[__main__]\nfoo=%(bar)s")
        expected = ('%(bar)s', set(['bar']))

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        result = parser._get_interpolation_keys('__main__', 'foo')
        self.assertEqual(result, expected)

    def test_get_interpolation_keys_bool(self):
        """Test get_interpolation_keys for a boolean."""
        class MySchema(Schema):
            foo = BoolOption()
        config = StringIO("[__main__]\nfoo=%(bar)s")
        expected = ('%(bar)s', set(['bar']))

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        result = parser._get_interpolation_keys('__main__', 'foo')
        self.assertEqual(result, expected)

    def test_get_interpolation_keys_tuple(self):
        """Test get_interpolation_keys for a tuple."""
        class MySchema(Schema):
            foo = TupleOption(2)
        config = StringIO("[__main__]\nfoo=%(bar)s,%(baz)s")
        expected = ('%(bar)s,%(baz)s', set(['bar', 'baz']))

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        result = parser._get_interpolation_keys('__main__', 'foo')
        self.assertEqual(result, expected)

    def test_get_interpolation_keys_lines(self):
        """Test get_interpolation_keys for a list."""
        class MySchema(Schema):
            foo = ListOption(item=StringOption())
        config = StringIO("[__main__]\nfoo=%(bar)s\n    %(baz)s")
        expected = ('%(bar)s\n%(baz)s', set(['bar', 'baz']))

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        result = parser._get_interpolation_keys('__main__', 'foo')
        self.assertEqual(result, expected)

    def test_get_interpolation_keys_tuple_lines(self):
        """Test get_interpolation_keys for a list of tuples."""
        class MySchema(Schema):
            foo = ListOption(item=TupleOption(2))
        config = StringIO(
            "[__main__]\nfoo=%(bar)s,%(bar)s\n    %(baz)s,%(baz)s")
        expected = ('%(bar)s,%(bar)s\n%(baz)s,%(baz)s',
                    set(['bar', 'baz']))

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        result = parser._get_interpolation_keys('__main__', 'foo')
        self.assertEqual(result, expected)

    def test_get_interpolation_keys_dict(self):
        """Test get_interpolation_keys for a dict."""
        class MySchema(Schema):
            foo = DictOption(spec={'a': IntOption()})
        config = StringIO(textwrap.dedent("""
            [__noschema__]
            bar=4
            [__main__]
            foo=mydict
            [mydict]
            a=%(bar)s
            """))
        expected = ('mydict', set([]))

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        result = parser._get_interpolation_keys('__main__', 'foo')
        self.assertEqual(result, expected)

    def test_interpolate_value_duplicate_key(self):
        """Test interpolate_value for a duplicate key."""
        class MySchema(Schema):
            foo = TupleOption(2)
        config = StringIO(
            "[__noschema__]\nbar=4\n[__main__]\nfoo=%(bar)s,%(bar)s")
        expected_value = '4,4'

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        value = parser._interpolate_value('__main__', 'foo')
        self.assertEqual(value, expected_value)

    def test_interpolate_value_invalid_key(self):
        """Test interpolate_value with an invalid key."""
        class MySchema(Schema):
            foo = TupleOption(2)
        config = StringIO("[other]\nbar=4\n[__main__]\nfoo=%(bar)s,%(bar)s")
        expected_value = None

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        value = parser._interpolate_value('__main__', 'foo')
        self.assertEqual(value, expected_value)

    def test_interpolate_value_no_keys(self):
        """Test interpolate_value with no keys."""
        class MySchema(Schema):
            foo = TupleOption(2)
        config = StringIO("[__main__]\nfoo=%(bar)s,%(bar)s")

        mock_get_interpolation_keys = Mock(return_value=('%(bar)s', None))

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        with patch.object(parser, '_get_interpolation_keys',
                mock_get_interpolation_keys):

            value = parser._interpolate_value('__main__', 'foo')
            self.assertEqual(value, None)

    def test_get_with_raw_value(self):
        """Test get using a raw value."""
        class MySchema(Schema):
            foo = StringOption(raw=True)
        config = StringIO('[__main__]\nfoo=blah%(asd)##$@@dddf2kjhkjs')
        expected_value = 'blah%(asd)##$@@dddf2kjhkjs'

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        value = parser.get('__main__', 'foo')
        self.assertEqual(value, expected_value)

    def test_interpolate_parse_dict(self):
        """Test interpolation while parsing a dict."""
        class MySchema(Schema):
            foo = DictOption(spec={'a': IntOption()})
        config = StringIO(textwrap.dedent("""
            [__noschema__]
            bar=4
            [__main__]
            foo=mydict
            [mydict]
            a=%(bar)s
            """))
        expected = {'__main__': {'foo': {'a': 4}}}

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        result = parser.values()
        self.assertEqual(result, expected)


class TestSchemaConfigParser(unittest.TestCase):
    def setUp(self):
        class MySchema(Schema):
            foo = StringOption()
        self.schema = MySchema()
        self.parser = SchemaConfigParser(self.schema)
        self.config = StringIO("[__main__]\nfoo = bar")

    def test_init_no_args(self):
        self.assertRaises(TypeError, SchemaConfigParser)

    def test_init_valid_schema(self):
        self.assertEqual(self.parser.schema, self.schema)

    def test_init_invalid_schema(self):
        class MyInvalidSchema(Schema):
            class __main__(Section):
                pass

        self.assertRaises(SchemaValidationError, SchemaConfigParser,
                          MyInvalidSchema())

    def test_items(self):
        self.parser.readfp(self.config)
        items = self.parser.items('__main__')
        self.assertEqual(set(items), set([('foo', 'bar')]))

    def test_items_no_section(self):
        self.assertRaises(NoSectionError, self.parser.items, '__main__')

    def test_items_raw(self):
        config = StringIO('[__main__]\nfoo=%(baz)s')
        self.parser.readfp(config)
        items = self.parser.items('__main__', raw=True)
        self.assertEqual(set(items), set([('foo', '%(baz)s')]))

    def test_items_vars(self):
        config = StringIO('[__main__]\nfoo=%(baz)s')
        self.parser.readfp(config)
        items = self.parser.items('__main__', vars={'baz': '42'})
        self.assertEqual(set(items), set([('foo', '42'), ('baz', '42')]))

    def test_items_interpolate(self):
        """Test parser.items with interpolated values."""
        class MySchema(Schema):
            foo = StringOption()

            class baz(Section):
                bar = StringOption()

        parser = SchemaConfigParser(MySchema())
        config = StringIO('[__main__]\nfoo=%(bar)s\n[baz]\nbar=42')
        parser.readfp(config)
        # test interpolate
        items = parser.items('baz')
        self.assertEqual(items, {'bar': '42'}.items())

    def test_items_interpolate_error(self):
        config = StringIO('[__main__]\nfoo=%(bar)s')
        self.parser.readfp(config)
        self.assertRaises(InterpolationMissingOptionError, self.parser.items,
                          '__main__')

    def test_values_empty_parser(self):
        values = self.parser.values()
        self.assertEqual(values, {'__main__': {'foo': ''}})

    def test_values_full_parser(self):
        expected_values = {'__main__': {'foo': 'bar'}}

        self.parser.readfp(self.config)
        values = self.parser.values()
        self.assertEqual(expected_values, values)
        values = self.parser.values(section='__main__')
        self.assertEqual(expected_values['__main__'], values)

    def test_values_many_sections_same_option(self):
        """Test parser.values for many section with the same option."""
        class MySchema(Schema):
            class foo(Section):
                bar = IntOption()

            class baz(Section):
                bar = IntOption()

        config = StringIO("[foo]\nbar=3\n[baz]\nbar=4")
        expected_values = {'foo': {'bar': 3}, 'baz': {'bar': 4}}

        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        values = parser.values()
        self.assertEqual(values, expected_values)

    def test_values_many_sections_different_options(self):
        """Test parser.values for many sections with different options."""
        class MySchema(Schema):
            class foo(Section):
                bar = IntOption()

            class bar(Section):
                baz = IntOption()

        config = StringIO("[foo]\nbar=3\n[bar]\nbaz=4")
        expected_values = {'foo': {'bar': 3}, 'bar': {'baz': 4}}

        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        values = parser.values()
        self.assertEqual(values, expected_values)

    def test_parse_option(self):
        """Test parser parses option."""
        class MyOtherSchema(Schema):
            class foo(Section):
                bar = StringOption()

        expected_value = 'baz'
        config = StringIO("[foo]\nbar = baz")
        parser = SchemaConfigParser(MyOtherSchema())
        parser.readfp(config)
        value = parser.get('foo', 'bar')
        self.assertEqual(value, expected_value)

    def test_parse_invalid_section(self):
        self.assertRaises(NoSectionError, self.parser.parse,
            'bar', 'baz', '1')

    def test_default_values(self):
        """Test parser reads default option values."""
        class MySchema(Schema):
            foo = BoolOption(default=True)

            class bar(Section):
                baz = IntOption()
                bla = StringOption(default='hello')

        schema = MySchema()
        config = StringIO("[bar]\nbaz=123")
        expected_values = {'__main__': {'foo': True},
                           'bar': {'baz': 123, 'bla': 'hello'}}
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEquals(expected_values, parser.values())

        config = StringIO("[bar]\nbla=123")
        expected = {
            '__main__': {'foo': True},
            'bar': {'baz': 0, 'bla': '123'}}
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEquals(expected, parser.values())

    def test_fatal_options(self):
        """Test parsing non-provided options marked as fatal."""
        class MySchema(Schema):
            foo = IntOption(fatal=True)
            bar = IntOption()
        schema = MySchema()
        config = StringIO("[__main__]\nfoo=123")
        expected = {'__main__': {'foo': 123, 'bar': 0}}
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEquals(expected, parser.values())

        config = StringIO("[__main__]\nbar=123")
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertRaises(NoOptionError, parser.values)

    def test_extra_sections(self):
        """Test extra_sections."""
        class MySchema(Schema):
            foo = DictOption(spec={'bar': IntOption()})

        config = StringIO("[__main__]\nfoo=mydict\n[mydict]\nbar=1")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        parser.parse_all()

        expected_sections = set(['mydict'])
        extra_sections = parser.extra_sections
        self.assertEqual(expected_sections, extra_sections)

    def test_extra_sections_dict_default_value(self):
        """Test parse dict with default value."""
        class MySchema(Schema):
            foo = DictOption(spec={
                'bar': IntOption(),
                'baz': BoolOption()})

        parser = SchemaConfigParser(MySchema())
        self.assertEqual(parser.get('__main__', 'foo'),
            {'bar': 0, 'baz': False})
        self.assertEqual(parser.extra_sections, set([]))

    def test_extra_sections_missing_section(self):
        """Test parse dict with missing referenced section."""
        class MySchema(Schema):
            foo = DictOption()

        config = StringIO(textwrap.dedent("""
            [__main__]
            foo = dict1
            """))
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        parser.parse_all()

        self.assertEqual(parser.extra_sections, set(['dict1']))

    def test_multiple_extra_sections(self):
        """Test parsing multiple extra sections."""
        class MySchema(Schema):
            foo = ListOption(
                item=DictOption(spec={'bar': IntOption()}))

        config = StringIO('[__main__]\nfoo=d1\n    d2\n    d3\n'
                          '[d1]\nbar=1\n[d2]\nbar=2\n[d3]\nbar=3')
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        parser.parse_all()

        expected_sections = set(['d1', 'd2', 'd3'])
        extra_sections = parser.extra_sections
        self.assertEqual(expected_sections, extra_sections)

    def test_get_default(self):
        config = StringIO("[__main__]\n")
        expected = ''
        self.parser.readfp(config)
        default = self.parser._get_default('__main__', 'foo')
        self.assertEqual(default, expected)

    def test_get_default_noschema(self):
        config = StringIO("[__noschema__]\nbar=1\n[__main__]\n")
        expected = '1'
        self.parser.readfp(config)
        default = self.parser._get_default('__noschema__', 'bar')
        self.assertEqual(default, expected)

    def test_get_default_from_section(self):
        """Test parser._get_default for a section/option pair."""
        class MySchema(Schema):
            class foo(Section):
                bar = IntOption()
        config = StringIO("[__main__]\n")
        expected = 0

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        default = parser._get_default('foo', 'bar')
        self.assertEqual(default, expected)

    def test_get_default_no_option(self):
        self.assertRaises(NoOptionError, self.parser._get_default,
            '__main__', 'bar')

    def test_get_default_no_section(self):
        self.assertRaises(NoSectionError, self.parser._get_default,
            'foo', 'bar')

    def test_multi_file_dict_config(self):
        """Test parsing a dict option spanning multiple files."""
        class MySchema(Schema):
            foo = DictOption(spec={
                'bar': IntOption(),
                'baz': IntOption(),
            }, strict=True)
        config1 = StringIO('[__main__]\nfoo=mydict\n[mydict]\nbar=1\nbaz=1')
        config2 = StringIO('[mydict]\nbaz=2')
        expected_values = {'__main__': {'foo': {'bar': 1, 'baz': 2}}}

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config1)
        parser.readfp(config2)
        self.assertEqual(parser.values(), expected_values)

    def test_multi_file_dict_list_config(self):
        """Test parsing a list of dicts option spanning multiple files."""
        class MySchema(Schema):
            foo = ListOption(
                item=DictOption(spec={
                    'bar': IntOption(),
                    'baz': IntOption(),
                }, strict=True))

        config1 = StringIO('[__main__]\nfoo=mydict\n[mydict]\nbar=1\nbaz=1')
        expected_values = {'__main__': {'foo': [{'bar': 1, 'baz': 1}]}}

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config1)
        self.assertEqual(parser.values(), expected_values)

        # override used dictionaries
        config2 = StringIO('[__main__]\nfoo=otherdict\n[otherdict]\nbar=2')
        expected_values = {'__main__': {'foo': [{'bar': 2, 'baz': 0}]}}
        parser.readfp(config2)
        self.assertEqual(parser.values(), expected_values)

        # override existing dictionaries
        config3 = StringIO('[otherdict]\nbaz=3')
        expected_values = {'__main__': {'foo': [{'bar': 2, 'baz': 3}]}}
        parser.readfp(config3)
        self.assertEqual(parser.values(), expected_values)

        # reuse existing dict
        config4 = StringIO('[__main__]\nfoo=mydict\n    otherdict')
        expected_values = {'__main__': {'foo': [{'bar': 1, 'baz': 1},
                                               {'bar': 2, 'baz': 3}]}}
        parser.readfp(config4)
        self.assertEqual(parser.values(), expected_values)

    def test_read_multiple_files(self):
        def setup_config():
            folder = tempfile.mkdtemp()

            f = open("%s/first.cfg" % folder, 'w')
            f.write("[__main__]\nfoo=foo")
            f.close()

            f = open("%s/second.cfg" % folder, 'w')
            f.write("[__main__]\nfoo=bar")
            f.close()

            files = ["%s/first.cfg" % folder, "%s/second.cfg" % folder]
            return files, folder

        files, folder = setup_config()
        self.parser.read(files)
        self.assertEqual(self.parser.values(), {'__main__': {'foo': 'bar'}})

        # silently remove any created files
        try:
            shutil.rmtree(folder)
        except:
            pass

    def test_read_utf8_encoded_file(self):
        # create config file
        fp, filename = tempfile.mkstemp()

        try:
            f = open(filename, 'w')
            f.write(u'[__main__]\nfoo=€'.encode(CONFIG_FILE_ENCODING))
            f.close()

            self.parser.read(filename)
            self.assertEqual(self.parser.values(),
                {'__main__': {'foo': u'€'}})
        finally:
            # destroy config file
            os.remove(filename)

    def test_readfp_with_utf8_encoded_text(self):
        config = StringIO(u'[__main__]\nfoo=€'.encode(CONFIG_FILE_ENCODING))
        self.parser.readfp(config)
        self.assertEqual(self.parser.values(), {'__main__': {'foo': u'€'}})

    def test_set(self):
        with tempfile.NamedTemporaryFile() as f:
            f.write('[__main__]\nfoo=1')
            f.flush()

            self.parser.read(f.name)
            self.assertEqual(self.parser._dirty, {})
            self.assertEqual(self.parser.get('__main__', 'foo'), '1')
            self.parser.set('__main__', 'foo', '2')
            self.assertEqual(self.parser.get('__main__', 'foo'), '2')
            self.assertEqual(self.parser._dirty,
                {f.name: {'__main__': {'foo': '2'}}})

    def test_set_non_string(self):
        """Test parser.set with a non-string value."""
        class MySchema(Schema):
            foo = IntOption()
            bar = BoolOption()
        parser = SchemaConfigParser(MySchema())
        parser.parse_all()

        parser.set('__main__', 'foo', 2)
        parser.set('__main__', 'bar', False)
        self.assertEqual(parser.get('__main__', 'foo'), 2)
        self.assertEqual(parser._sections['__main__']['foo'], '2')
        self.assertEqual(parser.get('__main__', 'bar'), False)
        self.assertEqual(parser._sections['__main__']['bar'], 'False')

    def test_set_invalid_type(self):
        self.parser.parse_all()
        self.assertRaises(TypeError, self.parser.set, '__main__', 'foo', 2)

    def test_write(self):
        """Test parser write config to a file."""
        class MySchema(Schema):
            foo = StringOption()

            class DEFAULTSECT(Section):
                pass

        parser = SchemaConfigParser(MySchema())
        expected = u"[{0}]\nbaz = 2\n\n[__main__]\nfoo = bar".format(
            DEFAULTSECT)
        config = StringIO(expected)
        parser.readfp(config)

        # create config file
        fp, filename = tempfile.mkstemp()
        try:
            parser.write(open(filename, 'w'))
            result = open(filename, 'r').read().strip()
            self.assertEqual(result, expected)
        finally:
            # remove the file
            os.unlink(filename)

    def test_write_prefill_parser(self):
        """Test parser write config to a file."""
        class MySchema(Schema):
            foo = IntOption()

        parser = SchemaConfigParser(MySchema())
        expected = u"[__main__]\nfoo = 0"

        # create config file
        fp, filename = tempfile.mkstemp()
        try:
            parser.write(open(filename, 'w'))
            result = open(filename, 'r').read().strip()
            self.assertEqual(result, expected)
        finally:
            # remove the file
            os.unlink(filename)

    def test_save_config(self):
        expected = u'[__main__]\nfoo = 42'
        self._check_save_file(expected)

    def test_save_config_non_ascii(self):
        expected = u'[__main__]\nfoo = fóobâr'
        self._check_save_file(expected)

    def _check_save_file(self, expected, read_config=True):
        config = StringIO(expected.encode(CONFIG_FILE_ENCODING))
        if read_config:
            self.parser.readfp(config)

        # create config file
        fp, filename = tempfile.mkstemp()
        try:
            self.parser.save(open(filename, 'w'))
            result = open(filename, 'r').read().strip()
            self.assertEqual(result.decode(CONFIG_FILE_ENCODING), expected)

            self.parser.save(filename)
            result = open(filename, 'r').read().strip()
            self.assertEqual(result.decode(CONFIG_FILE_ENCODING), expected)
        finally:
            # remove the file
            os.unlink(filename)

    def test_save_config_prefill_parser(self):
        """Test parser save config when no config files read."""
        expected = u'[__main__]\nfoo ='
        self._check_save_file(expected, read_config=False)

    def test_save_no_config_same_files(self):
        class MySchema(Schema):
            foo = IntOption()

        parser = SchemaConfigParser(MySchema())
        parser.set('__main__', 'foo', 2)
        self.assertRaises(ValueError, parser.save)

    def test_save_config_same_files(self):
        """Test parser save config values to original files."""
        def setup_config():
            folder = tempfile.mkdtemp()

            f = open("%s/first.cfg" % folder, 'w')
            f.write("[__main__]\nfoo=1")
            f.close()

            f = open("%s/second.cfg" % folder, 'w')
            f.write("[__main__]\nbar=2")
            f.close()

            files = ["%s/first.cfg" % folder, "%s/second.cfg" % folder]
            return files, folder

        class MySchema(Schema):
            foo = StringOption()
            bar = StringOption()
            baz = IntOption()

        self.parser = SchemaConfigParser(MySchema())

        files, folder = setup_config()
        self.parser.read(files)
        self.parser.set('__main__', 'foo', '42')
        self.parser.set('__main__', 'bar', '42')
        self.parser.set('__main__', 'baz', 42)
        self.parser.save()

        # test the changes were correctly saved
        data = open("%s/first.cfg" % folder).read()
        self.assertTrue('foo = 42' in data)
        self.assertFalse('bar = 42' in data)
        # new value goes into last read config file
        self.assertFalse('baz = 42' in data)
        data = open("%s/second.cfg" % folder).read()
        self.assertFalse('foo = 42' in data)
        self.assertTrue('bar = 42' in data)
        # new value goes into last read config file
        self.assertTrue('baz = 42' in data)

        # silently remove any created files
        try:
            shutil.rmtree(folder)
        except:
            pass

    def test_save_config_last_location_nested_includes(self):
        def setup_config():
            folder = tempfile.mkdtemp()

            f = open("%s/first.cfg" % folder, 'w')
            f.write("[__main__]\nfoo=1")
            f.close()

            f = open("%s/second.cfg" % folder, 'w')
            f.write("[__main__]\nbar=2\nincludes = third.cfg")
            f.close()

            f = open("%s/third.cfg" % folder, 'w')
            f.write("[__main__]\nfoo=3")
            f.close()

            files = ["%s/first.cfg" % folder, "%s/second.cfg" % folder]
            return files, folder

        class MySchema(Schema):
            foo = StringOption()
            bar = StringOption()
            baz = IntOption()

        self.parser = SchemaConfigParser(MySchema())

        files, folder = setup_config()
        self.parser.read(files)
        self.parser.set('__main__', 'foo', '42')
        self.parser.set('__main__', 'bar', '42')
        self.parser.set('__main__', 'baz', 42)
        self.parser.save()

        # test the changes were correctly saved
        data = open("%s/first.cfg" % folder).read()
        self.assertEqual(data.strip(), '[__main__]\nfoo=1')
        data = open("%s/third.cfg" % folder).read()
        self.assertEqual(data.strip(), '[__main__]\nfoo = 42')
        data = open("%s/second.cfg" % folder).read()
        self.assertTrue('bar = 42' in data)
        # new value goes into last read config file
        # not in the last included config file
        self.assertTrue('baz = 42' in data)

        # silently remove any created files
        try:
            shutil.rmtree(folder)
        except:
            pass


class TestParserIsValid(unittest.TestCase):
    def setUp(self):
        class MySchema(Schema):
            foo = StringOption()
        self.schema = MySchema()
        self.parser = SchemaConfigParser(self.schema)
        self.config = StringIO("[__main__]\nfoo = bar")

    def test_basic_is_valid(self):
        """Test basic validation without error reporting."""
        class MySchema(Schema):
            foo = IntOption()

        schema = MySchema()
        config = StringIO("[__main__]\nfoo = 5")
        parser = SchemaConfigParser(schema)
        parser.readfp(config)

        self.assertTrue(parser.is_valid())

    def test_basic_is_valid_with_report(self):
        """Test basic validation with error reporting."""
        class MySchema(Schema):
            foo = IntOption()

        config = StringIO("[__main__]\nfoo=5")
        expected = (True, [])
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        valid, errors = parser.is_valid(report=True)
        self.assertEqual((valid, errors), expected)

    def test_basic_is_not_valid(self):
        """Test invalid config without error reporting."""
        class MySchema(Schema):
            foo = IntOption()

        schema = MySchema()
        config = StringIO("[__main__]\nfoo = 5\nbar = 6")
        parser = SchemaConfigParser(schema)
        parser.readfp(config)

        self.assertFalse(parser.is_valid())

    def test_basic_is_not_valid_with_report(self):
        """Test invalid config with error reporting."""
        class MySchema(Schema):
            foo = IntOption()

        config = StringIO("[__main__]\nfoo=5\nbar=6")
        errors = ["Configuration includes invalid options for "
                  "section '__main__': bar"]
        expected = (False, errors)

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        valid, errors = parser.is_valid(report=True)
        self.assertEqual((valid, errors), expected)

    def test_is_not_valid_parser_error(self):
        """Test parser.is_valid when parser errors."""
        class MySchema(Schema):
            foo = IntOption()

        def mock_parse_all(self):
            assert False

        schema = MySchema()
        config = StringIO("[__main__]\nfoo = 5")
        parser = SchemaConfigParser(schema)
        parser.parse_all = mock_parse_all
        parser.readfp(config)

        self.assertFalse(parser.is_valid())

    def test_parse_invalid_section(self):
        config = StringIO("[bar]\nbaz=foo")
        self.parser.readfp(config)

        self.assertFalse(self.parser.is_valid())

    def test_parse_invalid_section_with_report(self):
        config = StringIO("[bar]\nbaz=foo")
        self.parser.readfp(config)

        valid, errors = self.parser.is_valid(report=True)
        self.assertFalse(valid)
        self.assertEqual(errors[0],
            u'Sections in configuration are missing from schema: bar')

    def test_different_sections(self):
        config = StringIO("[__main__]\nfoo=1\n[bar]\nbaz=2")
        self.parser.readfp(config)

        self.assertFalse(self.parser.is_valid())

    def test_missing_fatal_options(self):
        """Test parser.is_valid when missing fatal options."""
        class MySchema(Schema):
            foo = IntOption()
            bar = IntOption(fatal=True)

        config = StringIO("[__main__]\nfoo=1")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)

        self.assertFalse(parser.is_valid())

    def test_missing_nonfatal_options(self):
        """Test parser.is_valid when missing non-fatal options."""
        class MySchema(Schema):
            foo = IntOption()
            bar = IntOption(fatal=True)

        config = StringIO("[__main__]\nbar=2")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)

        self.assertTrue(parser.is_valid())

    def test_extra_sections(self):
        """Test parser.is_valid with extra sections."""
        class MySchema(Schema):
            foo = DictOption(spec={'bar': IntOption()})

        config = StringIO("[__main__]\nfoo=mydict\n[mydict]\nbar=1")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        parser.parse_all()

        self.assertTrue(parser.is_valid())

    def test_extra_sections_when_dict_with_nested_dicts(self):
        """Test parser.is_valid with extra sections in a nested dict."""
        class MySchema(Schema):
            foo = DictOption(item=DictOption())

        config = StringIO("""
[__main__]
foo=dict1
[dict1]
bar=dict2
[dict2]
baz=42
""")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        parser.parse_all()

        self.assertEqual(parser.values(),
            {'__main__': {'foo': {'bar': {'baz': '42'}}}})
        self.assertTrue(parser.is_valid())

    def test_extra_sections_with_nested_dicts_strict(self):
        """Test parser.is_valid w/ extra sections in a nested dict (strict)."""
        class MySchema(Schema):
            foo = DictOption(spec={'bar': DictOption()}, strict=True)

        config = StringIO("""
[__main__]
foo=dict1
[dict1]
bar=dict2
[dict2]
baz=42
""")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        parser.parse_all()

        self.assertEqual(parser.values(),
            {'__main__': {'foo': {'bar': {'baz': '42'}}}})
        self.assertTrue(parser.is_valid())

    def test_extra_sections_when_lines_dict_with_nested_dicts(self):
        """Test parser.is_valid w/ extra section in list of nested dicts."""
        class MySchema(Schema):
            foo = ListOption(
                item=DictOption(item=DictOption()))

        config = StringIO("""
[__main__]
foo = dict1
      dict2
[dict1]
bar = dict3
[dict2]
baz = dict4
[dict3]
wham = 1
[dict4]
whaz = 2
""")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        parser.parse_all()

        self.assertEqual(parser.values(),
            {'__main__': {'foo': [
                {'bar': {'wham': '1'}},
                {'baz': {'whaz': '2'}}]}})
        self.assertTrue(parser.is_valid())

    def test_extra_sections_when_dict_with_nested_lines_dicts(self):
        """Test parser.is_valid in dict of nested list lists."""
        class MySchema(Schema):
            foo = DictOption(
                item=ListOption(item=DictOption()))

        config = StringIO("""
[__main__]
foo = dict1
[dict1]
bar = dict2
      dict3
[dict2]
baz = 1
[dict3]
wham = 2
""")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        parser.parse_all()

        self.assertEqual(parser.values(),
            {'__main__': {'foo': {'bar': [{'baz': '1'}, {'wham': '2'}]}}})
        self.assertTrue(parser.is_valid())

    def test_extra_sections_when_lines_dict_with_nested_lines_dicts(self):
        """Test parser.is_valid in dict of nested dict lists."""
        class MySchema(Schema):
            foo = ListOption(
                item=DictOption(
                    item=ListOption(item=DictOption())))

        config = StringIO("""
[__main__]
foo = dict1
      dict2
[dict1]
bar = dict3
      dict4
[dict2]
baz = dict5
      dict6
[dict3]
wham = 1
[dict4]
whaz = 2
[dict5]
whoosh = 3
[dict6]
swoosh = 4
""")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        parser.parse_all()

        self.assertEqual(parser.values(),
            {'__main__': {'foo': [
                {'bar': [{'wham': '1'}, {'whaz': '2'}]},
                {'baz': [{'whoosh': '3'}, {'swoosh': '4'}]}]}})
        self.assertTrue(parser.is_valid())

    def test_extra_sections_with_missing_section(self):
        """Test parser.is_valid with dict referencing missing section."""
        class MySchema(Schema):
            foo = DictOption()

        config = StringIO(textwrap.dedent("""
            [__main__]
            foo = dict1
            """))
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        parser.parse_all()

        self.assertRaises(NoSectionError, parser.values)
        # config is not valid
        self.assertFalse(parser.is_valid())

    def test_multiple_extra_sections(self):
        """Test parser.is_valid with multiple extra sections."""
        class MySchema(Schema):
            foo = ListOption(
                item=DictOption(spec={'bar': IntOption()}))

        config = StringIO('[__main__]\nfoo=d1\n    d2\n    d3\n'
                          '[d1]\nbar=1\n[d2]\nbar=2\n[d3]\nbar=3')
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        parser.parse_all()

        self.assertTrue(parser.is_valid())

    def test_noschema_section(self):
        config = StringIO(
            "[__main__]\nfoo=%(bar)s\n[__noschema__]\nbar=hello")
        parser = SchemaConfigParser(self.schema)
        parser.readfp(config)
        parser.parse_all()

        self.assertTrue(parser.is_valid())

    def test_missing_schema_sections(self):
        class MySchema(Schema):
            class foo(Section):
                bar = IntOption()

            class bar(Section):
                baz = BoolOption()

        config = StringIO(textwrap.dedent("""
            [foo]
            bar = 3
            """))
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        parser.parse_all()

        self.assertTrue(parser.is_valid())


if __name__ == '__main__':
    unittest.main()
