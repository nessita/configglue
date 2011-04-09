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
from copy import deepcopy
from StringIO import StringIO

from configglue.pyschema.parser import SchemaConfigParser
from configglue.pyschema.schema import (
    BoolConfigOption,
    ConfigSection,
    DictConfigOption,
    IntConfigOption,
    LinesConfigOption,
    Schema,
    StringConfigOption,
    TupleConfigOption,
)


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
        class SchemaC(SchemaA):
            bar = ConfigSection()
            bar.woof = IntConfigOption()

        self.schema = SchemaB()
        self.other = SchemaC()

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

    def test_mutable_inherited(self):
        # modify one inherited attribute
        self.schema.foo.baz = IntConfigOption()

        # test on the other schema
        self.assertFalse(hasattr(self.other.foo, 'baz'))

    def test_merge_inherited(self):
        class SchemaA(Schema):
            foo = ConfigSection()
            foo.bar = IntConfigOption()
            bar = IntConfigOption()

        class SchemaB(SchemaA):
            foo = deepcopy(SchemaA.foo)
            foo.baz = IntConfigOption()

        # SchemaB inherits attributes from SchemaA and merges its own
        # attributes into
        schema = SchemaB()
        section_names = set(s.name for s in schema.sections())
        option_names = set(o.name for o in schema.options('__main__'))
        foo_option_names = set(o.name for o in schema.options('foo'))
        self.assertEqual(section_names, set(['__main__', 'foo']))
        self.assertEqual(option_names, set(['bar']))
        self.assertEqual(foo_option_names, set(['bar', 'baz']))

        # SchemaB inheritance does not affect SchemaA
        schema = SchemaA()
        section_names = set(s.name for s in schema.sections())
        option_names = set(o.name for o in schema.options('__main__'))
        foo_option_names = set(o.name for o in schema.options('foo'))
        self.assertEqual(section_names, set(['__main__', 'foo']))
        self.assertEqual(option_names, set(['bar']))
        self.assertEqual(foo_option_names, set(['bar']))


class TestStringConfigOption(unittest.TestCase):
    def setUp(self):
        self.opt = StringConfigOption()

    def test_init_no_args(self):
        self.assertFalse(self.opt.null)

    def test_init_null(self):
        opt = StringConfigOption(null=True)
        self.assertTrue(opt.null)

    def test_parse_ascii_string(self):
        value = self.opt.parse('42')
        self.assertEqual(value, '42')

    def test_parse_empty_string(self):
        value = self.opt.parse('')
        self.assertEqual(value, '')

    def test_parse_null_string(self):
        opt = StringConfigOption(null=True)
        value = opt.parse(None)
        self.assertEqual(value, None)

    def test_None_string(self):
        value = self.opt.parse('None')
        self.assertEqual(value, 'None')

    def test_parse_nonascii_string(self):
        foo = StringConfigOption()
        value = foo.parse('foóbâr')
        self.assertEqual(value, 'foóbâr')

    def test_parse_int(self):
        value = self.opt.parse(42)
        self.assertEqual(value, '42')

    def test_parse_bool(self):
        value = self.opt.parse(False)
        self.assertEqual(value, 'False')

    def test_default(self):
        opt = StringConfigOption()
        self.assertEqual(opt.default, '')

    def test_default_null(self):
        opt = StringConfigOption(null=True)
        self.assertEqual(opt.default, None)


class TestIntConfigOption(unittest.TestCase):
    def test_parse_int(self):
        class MySchema(Schema):
            foo = IntConfigOption()
        config = StringIO("[__main__]\nfoo = 42")
        expected_values = {'__main__': {'foo': 42}}
        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

        config = StringIO("[__main__]\nfoo =")
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertRaises(ValueError, parser.values)

        config = StringIO("[__main__]\nfoo = bla")
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertRaises(ValueError, parser.values)

    def test_default(self):
        opt = IntConfigOption()
        self.assertEqual(opt.default, 0)


class TestBoolConfigOption(unittest.TestCase):
    def test_parse_bool(self):
        class MySchema(Schema):
            foo = BoolConfigOption()
        config = StringIO("[__main__]\nfoo = Yes")
        expected_values = {'__main__': {'foo': True}}
        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

        config = StringIO("[__main__]\nfoo = tRuE")
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

        config = StringIO("[__main__]\nfoo =")
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertRaises(ValueError, parser.values)

        config = StringIO("[__main__]\nfoo = bla")
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertRaises(ValueError, parser.values)

    def test_default(self):
        opt = BoolConfigOption()
        self.assertEqual(opt.default, False)


class TestLinesConfigOption(unittest.TestCase):
    def test_parse_int_lines(self):
        class MySchema(Schema):
            foo = LinesConfigOption(item=IntConfigOption())

        config = StringIO("[__main__]\nfoo = 42\n 43\n 44")
        expected_values = {'__main__': {'foo': [42, 43, 44]}}
        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_bool_lines(self):
        class MySchema(Schema):
            foo = LinesConfigOption(item=BoolConfigOption())
        schema = MySchema()
        config = StringIO("[__main__]\nfoo = tRuE\n No\n 0\n 1")
        expected_values = {'__main__': {'foo': [True, False, False, True]}}
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEqual(expected_values, parser.values())

    def test_parse_bool_empty_lines(self):
        class MySchema(Schema):
            foo = LinesConfigOption(item=BoolConfigOption())
        schema = MySchema()
        config = StringIO("[__main__]\nfoo =")
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        expected_values = {'__main__': {'foo': []}}
        self.assertEqual(expected_values, parser.values())

    def test_parse_bool_invalid_lines(self):
        class MySchema(Schema):
            foo = LinesConfigOption(item=BoolConfigOption())
        schema = MySchema()
        config = StringIO("[__main__]\nfoo = bla")
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertRaises(ValueError, parser.values)

        config = StringIO("[__main__]\nfoo = True\n bla")
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertRaises(ValueError, parser.values)

    def test_default(self):
        opt = LinesConfigOption(item=IntConfigOption())
        self.assertEqual(opt.default, [])

    def test_remove_duplicates(self):
        class MySchema(Schema):
            foo = LinesConfigOption(item=StringConfigOption(),
                                    remove_duplicates=True)
        schema = MySchema()
        config = StringIO("[__main__]\nfoo = bla\n blah\n bla")
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEquals({'__main__': {'foo': ['bla', 'blah']}},
                          parser.values())

    def test_remove_dict_duplicates(self):
        class MyOtherSchema(Schema):
            foo = LinesConfigOption(item=DictConfigOption(),
                                    remove_duplicates=True)
        schema = MyOtherSchema()
        config = StringIO("[__main__]\nfoo = bla\n bla\n[bla]\nbar = baz")
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEquals({'__main__': {'foo': [{'bar': 'baz'}]}},
                          parser.values())

class TestTupleConfigOption(unittest.TestCase):
    def test_init(self):
        opt = TupleConfigOption(length=2)
        self.assertEqual(opt.length, 2)

    def test_init_no_length(self):
        opt = TupleConfigOption()
        self.assertEqual(opt.length, 0)
        self.assertEqual(opt.default, ())

    def test_parse_no_length(self):
        class MySchema(Schema):
            foo = TupleConfigOption()

        config = StringIO('[__main__]\nfoo=1,2,3,4')
        expected_values = {'__main__': {'foo': ('1', '2', '3', '4')}}
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_tuple(self):
        class MySchema(Schema):
            foo = TupleConfigOption(length=4)
        config = StringIO('[__main__]\nfoo = 1, 2, 3, 4')
        expected_values = {'__main__': {'foo': ('1', '2', '3', '4')}}
        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

        config = StringIO('[__main__]\nfoo = 1, 2, 3')
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertRaises(ValueError, parser.values)

        config = StringIO('[__main__]\nfoo = ')
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertRaises(ValueError, parser.values)

    def test_default(self):
        opt = TupleConfigOption(length=2)
        self.assertEqual(opt.default, ())


class TestDictConfigOption(unittest.TestCase):
    def test_init(self):
        opt = DictConfigOption()
        self.assertEqual(opt.spec, {})
        self.assertEqual(opt.strict, False)

        spec = {'a': IntConfigOption(), 'b': BoolConfigOption()}
        opt = DictConfigOption(spec=spec)
        self.assertEqual(opt.spec, spec)
        self.assertEqual(opt.strict, False)

        opt = DictConfigOption(spec=spec, strict=True)
        self.assertEqual(opt.spec, spec)
        self.assertEqual(opt.strict, True)

    def test_get_extra_sections(self):
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
        expected = ['dict2']

        opt = DictConfigOption(item=DictConfigOption())
        extra = opt.get_extra_sections('dict1', parser)
        self.assertEqual(extra, expected)

    def test_parse_dict(self):
        class MySchema(Schema):
            foo = DictConfigOption(spec={
                'bar': StringConfigOption(),
                'baz': IntConfigOption(),
                'bla': BoolConfigOption(),
            })
        config = StringIO("""[__main__]
foo = mydict
[mydict]
bar=baz
baz=42
bla=Yes
""")
        expected_values = {
            '__main__': {
                'foo': {'bar': 'baz', 'baz': 42, 'bla': True}
            }
        }

        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_raw(self):
        class MySchema(Schema):
            foo = DictConfigOption(spec={
                'bar': StringConfigOption(),
                'baz': IntConfigOption(),
                'bla': BoolConfigOption(),
            })
        config = StringIO("""[__main__]
foo = mydict
[mydict]
baz=42
""")
        expected = {'bar': '', 'baz': '42', 'bla': 'False'}

        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        parsed = schema.foo.parse('mydict', parser, True)
        self.assertEqual(parsed, expected)

    def test_parse_invalid_key_in_parsed(self):
        class MySchema(Schema):
            foo = DictConfigOption(spec={'bar': IntConfigOption()})

        config = StringIO("[__main__]\nfoo=mydict\n[mydict]\nbaz=2")
        expected_values = {'__main__': {'foo': {'bar': 0, 'baz': '2'}}}
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_invalid_key_in_spec(self):
        class MySchema(Schema):
            foo = DictConfigOption(spec={
                'bar': IntConfigOption(),
                'baz': IntConfigOption(fatal=True)})

        config = StringIO("[__main__]\nfoo=mydict\n[mydict]\nbar=2")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertRaises(ValueError, parser.parse_all)

    def test_default(self):
        opt = DictConfigOption(spec={})
        self.assertEqual(opt.default, {})

    def test_parse_no_strict_missing_args(self):
        class MySchema(Schema):
            foo = DictConfigOption(spec={'bar': IntConfigOption()})

        config = StringIO("[__main__]\nfoo=mydict\n[mydict]")
        expected_values = {'__main__': {'foo': {'bar': 0}}}
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_no_strict_extra_args(self):
        class MySchema(Schema):
            foo = DictConfigOption()

        config = StringIO("[__main__]\nfoo=mydict\n[mydict]\nbar=2")
        expected_values = {'__main__': {'foo': {'bar': '2'}}}
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_no_strict_with_item(self):
        class MySchema(Schema):
            foo = DictConfigOption(
                      item=DictConfigOption(
                          item=IntConfigOption()))
        config = StringIO("""
[__main__]
foo = mydict
[mydict]
bar = baz
[baz]
wham=42
""")
        expected_values = {'__main__': {'foo': {'bar': {'wham': 42}}}}
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_strict(self):
        class MySchema(Schema):
            spec = {'bar': IntConfigOption()}
            foo = DictConfigOption(spec=spec, strict=True)

        config = StringIO("[__main__]\nfoo=mydict\n[mydict]\nbar=2")
        expected_values = {'__main__': {'foo': {'bar': 2}}}
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_strict_missing_vars(self):
        class MySchema(Schema):
            spec = {'bar': IntConfigOption(),
                    'baz': IntConfigOption()}
            foo = DictConfigOption(spec=spec, strict=True)

        config = StringIO("[__main__]\nfoo=mydict\n[mydict]\nbar=2")
        expected_values = {'__main__': {'foo': {'bar': 2, 'baz': 0}}}
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_strict_extra_vars(self):
        class MySchema(Schema):
            spec = {'bar': IntConfigOption()}
            foo = DictConfigOption(spec=spec, strict=True)

        config = StringIO("[__main__]\nfoo=mydict\n[mydict]\nbar=2\nbaz=3")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertRaises(ValueError, parser.parse_all)


class TestLinesOfDictConfigOption(unittest.TestCase):
    def test_parse_lines_of_dict(self):
        class MySchema(Schema):
            foo = LinesConfigOption(item=DictConfigOption(
                spec={
                    'bar': StringConfigOption(),
                    'baz': IntConfigOption(),
                    'bla': BoolConfigOption(),
                }))
        config = StringIO("""[__main__]
foo = mylist0
      mylist1
[mylist0]
bar=baz
baz=42
bla=Yes
[mylist1]
bar=zort
baz=123
bla=0
""")
        expected_values = {
            '__main__': {'foo': [{'bar': 'baz', 'baz': 42, 'bla': True},
                                {'bar': 'zort', 'baz': 123, 'bla': False},
                               ]}}

        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)


class TestDictWithDicts(unittest.TestCase):
    def test_parse_dict_with_dicts(self):
        innerspec = {'bar': StringConfigOption(),
                     'baz': IntConfigOption(),
                     'bla': BoolConfigOption(),
                    }
        spec = {'name': StringConfigOption(),
                'size': IntConfigOption(),
                'options': DictConfigOption(spec=innerspec)}
        class MySchema(Schema):
            foo = DictConfigOption(spec=spec)
        config = StringIO("""[__main__]
foo = outerdict
[outerdict]
options = innerdict
[innerdict]
bar = something
baz = 42
""")
        expected_values = {
            '__main__': {'foo': {'name': '', 'size': 0,
                                'options': {'bar': 'something', 'baz': 42,
                                            'bla': False}}}}
        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)


class TestListOfTuples(unittest.TestCase):
    def setUp(self):
        class MySchema(Schema):
            foo = LinesConfigOption(item=TupleConfigOption(length=3))
        schema = MySchema()
        self.parser = SchemaConfigParser(schema)

    def test_parse_list_of_tuples(self):
        config = StringIO('[__main__]\nfoo = a, b, c\n      d, e, f')
        expected_values = {
            '__main__': {'foo': [('a', 'b', 'c'), ('d', 'e', 'f')]}}
        self.parser.readfp(config)
        self.assertEqual(self.parser.values(), expected_values)

    def test_parse_wrong_tuple_size(self):
        config = StringIO('[__main__]\nfoo = a, b, c\n      d, e')
        self.parser.readfp(config)
        self.assertRaises(ValueError, self.parser.values)

    def test_parse_empty_tuple(self):
        config = StringIO('[__main__]\nfoo=()')
        expected_values = {'__main__': {'foo': [()]}}
        self.parser.readfp(config)
        self.assertEqual(self.parser.values(), expected_values)

