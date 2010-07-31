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

# -*- coding: utf-8 -*-
# Copyright 2010 Canonical Ltd.  This software is licensed under the
# GNU Lesser General Public License version 3 (see the file LICENSE).

import os
import shutil
import tempfile
import unittest
from StringIO import StringIO

from ConfigParser import (InterpolationMissingOptionError,
    InterpolationDepthError, NoSectionError)

from configglue.pyschema import ConfigSection
from configglue.pyschema.options import (BoolConfigOption, DictConfigOption,
    IntConfigOption, StringConfigOption, LinesConfigOption, TupleConfigOption)
from configglue.pyschema.schema import Schema
from configglue.pyschema.parser import (NoOptionError, SchemaConfigParser,
    SchemaValidationError, CONFIG_FILE_ENCODING)


class TestIncludes(unittest.TestCase):
    def setUp(self):
        class MySchema(Schema):
            foo = StringConfigOption()
        self.schema = MySchema()
        fd, self.name = tempfile.mkstemp(suffix='.cfg')
        os.write(fd, '[__main__]\nfoo=bar\n')
        os.close(fd)

    def tearDown(self):
        os.remove(self.name)

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

    def test_read_ioerror(self):
        def mock_open(filename, mode='r', encoding='ascii'):
            raise IOError
        _open = __builtins__['open']
        __builtins__['open'] = mock_open

        parser = SchemaConfigParser(self.schema)
        read_ok = parser.read(self.name)
        self.assertEqual(read_ok, [])

        __builtins__['open'] = _open

    def test_relative_include(self):
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
            foo = IntConfigOption()
            bar = IntConfigOption()
            baz = IntConfigOption()

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
        def setup_config():
            folder = tempfile.mkdtemp()

            f = open("%s/first.cfg" % folder, 'w')
            f.write("[__main__]\nfoo=1\nbar=2\nincludes=second.cfg")
            f.close()

            f = open("%s/second.cfg" % folder, 'w')
            f.write("[__main__]\nbaz=3")
            f.close()

            config = StringIO("[__main__]\nfoo=4\nincludes=%s/first.cfg" % folder)
            return config, folder

        class MySchema(Schema):
            foo = IntConfigOption()
            bar = IntConfigOption()
            baz = IntConfigOption()

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
    def test_basic_interpolate(self):
        class MySchema(Schema):
            foo = StringConfigOption()
            bar = BoolConfigOption()
        config = StringIO('[__main__]\nbar=%(foo)s\nfoo=True')
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config, 'my.cfg')
        self.assertEquals({'__main__': {'foo': 'True', 'bar': True}},
                          parser.values())

    def test_interpolate_missing_option(self):
        class MySchema(Schema):
            foo = StringConfigOption()
            bar = BoolConfigOption()

        section = '__main__'
        option = 'foo'
        rawval = '%(baz)s'
        vars = {}
        parser = SchemaConfigParser(MySchema())
        self.assertRaises(InterpolationMissingOptionError,
            parser._interpolate, section, option, rawval, vars)

    def test_interpolate_too_deep(self):
        class MySchema(Schema):
            foo = StringConfigOption()
            bar = BoolConfigOption()

        section = '__main__'
        option = 'foo'
        rawval = '%(bar)s'
        vars = {'foo': '%(bar)s', 'bar': '%(foo)s'}
        parser = SchemaConfigParser(MySchema())
        self.assertRaises(InterpolationDepthError,
            parser._interpolate, section, option, rawval, vars)

    def test_interpolate_incomplete_format(self):
        class MySchema(Schema):
            foo = StringConfigOption()
            bar = BoolConfigOption()

        section = '__main__'
        option = 'foo'
        rawval = '%(bar)'
        vars = {'foo': '%(bar)s', 'bar': 'pepe'}
        parser = SchemaConfigParser(MySchema())
        self.assertRaises(ValueError, parser._interpolate, section, option,
                          rawval, vars)

    def test_interpolate_across_sections(self):
        class MySchema(Schema):
            foo = ConfigSection()
            foo.bar = IntConfigOption()

            baz = ConfigSection()
            baz.wham = IntConfigOption()

        config = StringIO("[foo]\nbar=%(wham)s\n[baz]\nwham=42")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertRaises(InterpolationMissingOptionError,
            parser.get, 'foo', 'bar')

    def test_interpolate_invalid_key(self):
        class MySchema(Schema):
            foo = ConfigSection()
            foo.bar = IntConfigOption()

            baz = ConfigSection()
            baz.wham = IntConfigOption()

        config = StringIO("[foo]\nbar=%(wham)\n[baz]\nwham=42")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertRaises(InterpolationMissingOptionError, parser.get,
                          'foo', 'bar')

    def test_get_interpolation_keys_string(self):
        class MySchema(Schema):
            foo = StringConfigOption()
        config = StringIO("[__main__]\nfoo=%(bar)s")
        expected = ('%(bar)s', set(['bar']))

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        result = parser._get_interpolation_keys('__main__', 'foo')
        self.assertEqual(result, expected)

    def test_get_interpolation_keys_int(self):
        class MySchema(Schema):
            foo = IntConfigOption()
        config = StringIO("[__main__]\nfoo=%(bar)s")
        expected = ('%(bar)s', set(['bar']))

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        result = parser._get_interpolation_keys('__main__', 'foo')
        self.assertEqual(result, expected)

    def test_get_interpolation_keys_bool(self):
        class MySchema(Schema):
            foo = BoolConfigOption()
        config = StringIO("[__main__]\nfoo=%(bar)s")
        expected = ('%(bar)s', set(['bar']))

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        result = parser._get_interpolation_keys('__main__', 'foo')
        self.assertEqual(result, expected)

    def test_get_interpolation_keys_tuple(self):
        class MySchema(Schema):
            foo = TupleConfigOption(2)
        config = StringIO("[__main__]\nfoo=%(bar)s,%(baz)s")
        expected = ('%(bar)s,%(baz)s', set(['bar', 'baz']))

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        result = parser._get_interpolation_keys('__main__', 'foo')
        self.assertEqual(result, expected)

    def test_get_interpolation_keys_lines(self):
        class MySchema(Schema):
            foo = LinesConfigOption(item=StringConfigOption())
        config = StringIO("[__main__]\nfoo=%(bar)s\n    %(baz)s")
        expected = ('%(bar)s\n%(baz)s', set(['bar', 'baz']))

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        result = parser._get_interpolation_keys('__main__', 'foo')
        self.assertEqual(result, expected)

    def test_get_interpolation_keys_tuple_lines(self):
        class MySchema(Schema):
            foo = LinesConfigOption(item=TupleConfigOption(2))
        config = StringIO("[__main__]\nfoo=%(bar)s,%(bar)s\n    %(baz)s,%(baz)s")
        expected = ('%(bar)s,%(bar)s\n%(baz)s,%(baz)s',
                    set(['bar', 'baz']))

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        result = parser._get_interpolation_keys('__main__', 'foo')
        self.assertEqual(result, expected)

    def test_get_interpolation_keys_dict(self):
        class MySchema(Schema):
            foo = DictConfigOption({'a': IntConfigOption()})
        config = StringIO("[__noschema__]\nbar=4\n[__main__]\nfoo=mydict\n[mydict]\na=%(bar)s")
        expected = ('mydict', set([]))

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        result = parser._get_interpolation_keys('__main__', 'foo')
        self.assertEqual(result, expected)

    def test_interpolate_value_duplicate_key(self):
        class MySchema(Schema):
            foo = TupleConfigOption(2)
        config = StringIO("[__noschema__]\nbar=4\n[__main__]\nfoo=%(bar)s,%(bar)s")
        expected_value = '4,4'

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        value = parser._interpolate_value('__main__', 'foo')
        self.assertEqual(value, expected_value)

    def test_interpolate_value_invalid_key(self):
        class MySchema(Schema):
            foo = TupleConfigOption(2)
        config = StringIO("[other]\nbar=4\n[__main__]\nfoo=%(bar)s,%(bar)s")
        expected_value = None

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        value = parser._interpolate_value('__main__', 'foo')
        self.assertEqual(value, expected_value)

    def test_get_with_raw_value(self):
        class MySchema(Schema):
            foo = StringConfigOption(raw=True)
        config = StringIO('[__main__]\nfoo=blah%(asd)##$@@dddf2kjhkjs')
        expected_value = 'blah%(asd)##$@@dddf2kjhkjs'

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        value = parser.get('__main__', 'foo')
        self.assertEqual(value, expected_value)

    def test_interpolate_parse_dict(self):
        class MySchema(Schema):
            foo = DictConfigOption({'a': IntConfigOption()})
        config = StringIO("[__noschema__]\nbar=4\n[__main__]\nfoo=mydict\n[mydict]\na=%(bar)s")
        expected = {'__main__': {'foo': {'a': 4}}}

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        result = parser.values()
        self.assertEqual(result, expected)


class TestSchemaConfigParser(unittest.TestCase):
    def setUp(self):
        class MySchema(Schema):
            foo = StringConfigOption()
        self.schema = MySchema()
        self.parser = SchemaConfigParser(self.schema)
        self.config = StringIO("[__main__]\nfoo = bar")

    def test_init_no_args(self):
        self.assertRaises(TypeError, SchemaConfigParser)

    def test_init_valid_schema(self):
        self.assertEqual(self.parser.schema, self.schema)

    def test_init_invalid_schema(self):
        class MyInvalidSchema(Schema):
            __main__ = ConfigSection()

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
        class MySchema(Schema):
            foo = StringConfigOption()
            baz = ConfigSection()
            baz.bar = StringConfigOption()

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
        class MySchema(Schema):
            foo = ConfigSection()
            foo.bar = IntConfigOption()

            baz = ConfigSection()
            baz.bar = IntConfigOption()

        config = StringIO("[foo]\nbar=3\n[baz]\nbar=4")
        expected_values = {'foo': {'bar': 3}, 'baz': {'bar': 4}}

        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        values = parser.values()
        self.assertEqual(values, expected_values)

    def test_values_many_sections_different_options(self):
        class MySchema(Schema):
            foo = ConfigSection()
            foo.bar = IntConfigOption()

            bar = ConfigSection()
            bar.baz = IntConfigOption()

        config = StringIO("[foo]\nbar=3\n[bar]\nbaz=4")
        expected_values = {'foo': {'bar': 3}, 'bar': {'baz': 4}}

        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        values = parser.values()
        self.assertEqual(values, expected_values)

    def test_parse_option(self):
        class MyOtherSchema(Schema):
            foo = ConfigSection()
            foo.bar = StringConfigOption()

        expected_value = 'baz'
        config = StringIO("[foo]\nbar = baz")
        parser = SchemaConfigParser(MyOtherSchema())
        parser.readfp(config)
        value = parser.get('foo', 'bar')
        self.assertEqual(value, expected_value)

    def test_parse_invalid_section(self):
        self.assertRaises(NoSectionError, self.parser.parse, 'bar', 'baz', '1')

    def test_default_values(self):
        class MySchema(Schema):
            foo = BoolConfigOption(default=True)
            bar = ConfigSection()
            bar.baz = IntConfigOption()
            bar.bla = StringConfigOption(default='hello')
        schema = MySchema()
        config = StringIO("[bar]\nbaz=123")
        expected_values = {'__main__': {'foo': True},
                           'bar': {'baz': 123, 'bla': 'hello'}}
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEquals(expected_values, parser.values())

        config = StringIO("[bar]\nbla=123")
        expected = {'__main__': {'foo': True}, 'bar': {'baz': 0, 'bla': '123'}}
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEquals(expected, parser.values())

    def test_fatal_options(self):
        class MySchema(Schema):
            foo = IntConfigOption(fatal=True)
            bar = IntConfigOption()
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
        class MySchema(Schema):
            foo = DictConfigOption({'bar': IntConfigOption()})

        config = StringIO("[__main__]\nfoo=mydict\n[mydict]\nbar=1")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        parser.parse_all()

        expected_sections = set(['mydict'])
        extra_sections = parser.extra_sections
        self.assertEqual(expected_sections, extra_sections)

    def test_multiple_extra_sections(self):
        class MySchema(Schema):
            foo = LinesConfigOption(
                item=DictConfigOption({'bar': IntConfigOption()}))

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
        class MySchema(Schema):
            foo = ConfigSection()
            foo.bar = IntConfigOption()
        config = StringIO("[__main__]\n")
        expected = '0'

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        default = parser._get_default('foo', 'bar')
        self.assertEqual(default, expected)

    def test_get_default_no_option(self):
        expected = None
        default = self.parser._get_default('__main__', 'bar')
        self.assertEqual(default, expected)

    def test_get_default_no_section(self):
        expected = None
        default = self.parser._get_default('foo', 'bar')
        self.assertEqual(default, expected)

    def test_multi_file_dict_config(self):
        class MySchema(Schema):
            foo = DictConfigOption({'bar': IntConfigOption(),
                                    'baz': IntConfigOption()},
                                   strict=True)
        config1 = StringIO('[__main__]\nfoo=mydict\n[mydict]\nbar=1\nbaz=1')
        config2 = StringIO('[mydict]\nbaz=2')
        expected_values = {'__main__': {'foo': {'bar': 1, 'baz': 2}}}

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config1)
        parser.readfp(config2)
        self.assertEqual(parser.values(), expected_values)

    def test_multi_file_dict_list_config(self):
        class MySchema(Schema):
            foo = LinesConfigOption(
                item=DictConfigOption({'bar': IntConfigOption(),
                                       'baz': IntConfigOption()},
                                      strict=True))

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
            self.assertEqual(self.parser.values(), {'__main__': {'foo': u'€'}})
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

    def test_save_config(self):
        expected_output = u'[__main__]\nfoo = 42\n\n'
        config = StringIO(u'[__main__]\nfoo=42')
        self.parser.readfp(config)

        # create config file
        fp, filename = tempfile.mkstemp()
        self.parser.save(open(filename, 'w'))
        self.assertEqual(open(filename, 'r').read(), expected_output)

        self.parser.save(filename)
        self.assertEqual(open(filename, 'r').read(), expected_output)

        # remove the file
        os.unlink(filename)

    def test_save_config_same_files(self):
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
            foo = StringConfigOption()
            bar = StringConfigOption()

        self.parser = SchemaConfigParser(MySchema())

        files, folder = setup_config()
        self.parser.read(files)
        self.parser.set('__main__', 'foo', '42')
        self.parser.set('__main__', 'bar', '42')
        self.parser.save()

        # test the changes were correctly saved
        data = open("%s/first.cfg" % folder).read()
        self.assertTrue('foo = 42' in data)
        self.assertFalse('bar = 42' in data)
        data = open("%s/second.cfg" % folder).read()
        self.assertFalse('foo = 42' in data)
        self.assertTrue('bar = 42' in data)

        # silently remove any created files
        try:
            shutil.rmtree(folder)
        except:
            pass


class TestParserIsValid(unittest.TestCase):
    def setUp(self):
        class MySchema(Schema):
            foo = StringConfigOption()
        self.schema = MySchema()
        self.parser = SchemaConfigParser(self.schema)
        self.config = StringIO("[__main__]\nfoo = bar")

    def test_basic_is_valid(self):
        class MySchema(Schema):
            foo = IntConfigOption()

        schema = MySchema()
        config = StringIO("[__main__]\nfoo = 5")
        parser = SchemaConfigParser(schema)
        parser.readfp(config)

        self.assertTrue(parser.is_valid())

    def test_basic_is_valid_with_report(self):
        class MySchema(Schema):
            foo = IntConfigOption()

        config = StringIO("[__main__]\nfoo=5")
        expected = (True, [])
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        valid, errors = parser.is_valid(report=True)
        self.assertEqual((valid, errors), expected)

    def test_basic_is_not_valid(self):
        class MySchema(Schema):
            foo = IntConfigOption()

        schema = MySchema()
        config = StringIO("[__main__]\nfoo = 5\nbar = 6")
        parser = SchemaConfigParser(schema)
        parser.readfp(config)

        self.assertFalse(parser.is_valid())

    def test_basic_is_not_valid_with_report(self):
        class MySchema(Schema):
            foo = IntConfigOption()

        config = StringIO("[__main__]\nfoo=5\nbar=6")
        errors = ["Configuration includes invalid options for section '__main__': bar"]
        expected = (False, errors)

        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        valid, errors = parser.is_valid(report=True)
        self.assertEqual((valid, errors), expected)

    def test_is_not_valid_parser_error(self):
        class MySchema(Schema):
            foo = IntConfigOption()

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

    def test_different_sections(self):
        config = StringIO("[__main__]\nfoo=1\n[bar]\nbaz=2")
        self.parser.readfp(config)

        self.assertFalse(self.parser.is_valid())

    def test_missing_fatal_options(self):
        class MySchema(Schema):
            foo = IntConfigOption()
            bar = IntConfigOption(fatal=True)

        config = StringIO("[__main__]\nfoo=1")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)

        self.assertFalse(parser.is_valid())

    def test_missing_nonfatal_options(self):
        class MySchema(Schema):
            foo = IntConfigOption()
            bar = IntConfigOption(fatal=True)

        config = StringIO("[__main__]\nbar=2")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)

        self.assertTrue(parser.is_valid())

    def test_extra_sections(self):
        class MySchema(Schema):
            foo = DictConfigOption({'bar': IntConfigOption()})

        config = StringIO("[__main__]\nfoo=mydict\n[mydict]\nbar=1")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        parser.parse_all()

        self.assertTrue(parser.is_valid())

    def test_extra_sections_when_dict_with_nested_dicts(self):
        class MySchema(Schema):
            foo = DictConfigOption(item=DictConfigOption())

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
        class MySchema(Schema):
            foo = DictConfigOption({'bar': DictConfigOption()}, strict=True)

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
        class MySchema(Schema):
            foo = LinesConfigOption(
                item=DictConfigOption(item=DictConfigOption()))

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
                {'baz': {'whaz': '2'}}
            ]}})
        self.assertTrue(parser.is_valid())

    def test_extra_sections_when_dict_with_nested_lines_dicts(self):
        class MySchema(Schema):
            foo = DictConfigOption(
                item=LinesConfigOption(item=DictConfigOption()))

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
        class MySchema(Schema):
            foo = LinesConfigOption(
                item=DictConfigOption(
                    item=LinesConfigOption(item=DictConfigOption())))

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
                {'baz': [{'whoosh': '3'}, {'swoosh': '4'}]}
            ]}})
        self.assertTrue(parser.is_valid())

    def test_multiple_extra_sections(self):
        class MySchema(Schema):
            foo = LinesConfigOption(
                item=DictConfigOption({'bar': IntConfigOption()}))

        config = StringIO('[__main__]\nfoo=d1\n    d2\n    d3\n'
                          '[d1]\nbar=1\n[d2]\nbar=2\n[d3]\nbar=3')
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        parser.parse_all()

        self.assertTrue(parser.is_valid())

    def test_noschema_section(self):
        config = StringIO("[__main__]\nfoo=%(bar)s\n[__noschema__]\nbar=hello")
        parser = SchemaConfigParser(self.schema)
        parser.readfp(config)
        parser.parse_all()

        self.assertTrue(parser.is_valid())


if __name__ == '__main__':
    unittest.main()