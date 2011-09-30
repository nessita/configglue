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

import textwrap
import unittest
from ConfigParser import (
    NoOptionError,
    NoSectionError,
)
from StringIO import StringIO

from configglue.parser import (
    SchemaConfigParser,
    SchemaValidationError,
)
from configglue.schema import (
    BoolOption,
    Option,
    Section,
    DictOption,
    IntOption,
    ListOption,
    Schema,
    StringOption,
    TupleOption,
    get_config_objects,
    merge,
)


class TestSchema(unittest.TestCase):
    def test_sections(self):
        """Test Schema sections."""
        class MySchema(Schema):
            foo = BoolOption()

        class MyOtherSchema(Schema):
            class web(Section):
                bar = IntOption()

            class froo(Section):
                twaddle = ListOption(item=BoolOption())

        class MyThirdSchema(Schema):
            bar = IntOption()

            class froo(Section):
                twaddle = ListOption(item=BoolOption())

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
        """Test Schema validation."""
        class BorkenSchema(Schema):
            class __main__(Section):
                foo = BoolOption()

        class SomeSchema(Schema):
            class mysection(Section):
                pass

        schema = BorkenSchema()
        self.assertFalse(schema.is_valid())

        schema = SomeSchema()
        self.assertTrue(schema.is_valid())

    def test_names(self):
        """Test Schema section/option names."""
        class MySchema(Schema):
            foo = BoolOption()

            class bar(Section):
                baz = IntOption()

        schema = MySchema()
        self.assertEquals('foo', schema.foo.name)
        self.assertEquals('__main__', schema.foo.section.name)
        self.assertEquals('bar', schema.bar.name)
        self.assertEquals('baz', schema.bar.baz.name)
        self.assertEquals('bar', schema.bar.baz.section.name)

    def test_options(self):
        """Test Schema options."""
        class MySchema(Schema):
            foo = BoolOption()

            class bar(Section):
                baz = IntOption()

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
        """Test Schema equality."""
        class MySchema(Schema):
            foo = IntOption()

        class OtherSchema(Schema):
            bar = IntOption()

        self.assertEqual(MySchema(), MySchema())
        self.assertNotEqual(MySchema(), OtherSchema())


class TestSchemaHelpers(unittest.TestCase):
    def test_get_config_objects(self):
        """Test get_config_objects."""
        class MySchema(Schema):
            foo = IntOption()

            class one(Section):
                bar = IntOption()

            two = Section()
            two.bam = IntOption()

        expected = {
            'foo': MySchema.foo,
            'one': MySchema.one(),
            'two': MySchema.two,
        }
        objects = dict(get_config_objects(MySchema))
        self.assertEqual(objects.keys(), expected.keys())
        # cannot compare for just equal as inner classes are
        # instantiated when get_config_objects is called
        for key, value in expected.items():
            self.assertEqual(type(objects[key]), type(value))


class TestOption(unittest.TestCase):
    cls = Option

    def test_equal(self):
        """Test option equality."""
        opt1 = IntOption(name='opt1')
        opt2 = IntOption(name='opt2')
        opt3 = StringOption(name='opt1')
        self.assertEqual(opt1, opt1)
        self.assertNotEqual(opt1, opt2)
        self.assertNotEqual(opt1, opt3)

    def test_equal_when_in_section(self):
        """Test option equality for section options."""
        sect1 = Section(name='sect1')
        sect2 = Section(name='sect2')
        opt1 = IntOption()
        opt2 = IntOption()

        self.assertEqual(opt1, opt2)

        opt1.section = sect1
        opt2.section = sect2
        self.assertNotEqual(opt1, opt2)

    def test_equal_when_error(self):
        """Test option equality when errors."""
        opt1 = IntOption()
        opt2 = IntOption()

        # make sure an attribute error is raised
        del opt2.name
        self.assertNotEqual(opt1, opt2)

    def test_validate(self):
        """Test Option default validate behaviour."""
        opt = self.cls()
        self.assertRaises(NotImplementedError, opt.validate, 0)

    def test_short_name(self):
        """Test Option short name."""
        opt = self.cls(short_name='f')
        self.assertEqual(opt.short_name, 'f')


class TestSchemaInheritance(unittest.TestCase):
    def setUp(self):
        class SchemaA(Schema):
            class foo(Section):
                bar = IntOption()

        class SchemaB(SchemaA):
            class baz(Section):
                wham = IntOption()

        class SchemaC(SchemaA):
            class bar(Section):
                woof = IntOption()

        self.schema = SchemaB()
        self.other = SchemaC()

    def test_basic_inheritance(self):
        """Test basic schema inheritance."""
        names = [('foo', ['bar']), ('baz', ['wham'])]
        for section, options in names:
            section_obj = getattr(self.schema, section)
            self.assertTrue(isinstance(section_obj, Section))
            for option in options:
                option_obj = getattr(section_obj, option)
                self.assertTrue(isinstance(option_obj, IntOption))

    def test_inherited_sections(self):
        names = set(s.name for s in self.schema.sections())
        self.assertEqual(set(['foo', 'baz']), names)

    def test_inherited_options(self):
        names = set(s.name for s in self.schema.options())
        self.assertEqual(set(['bar', 'wham']), names)

    def test_mutable_inherited(self):
        """Test modifying inherited attribute doesn't affect parent."""
        # modify one inherited attribute
        self.schema.foo.baz = IntOption()

        # test on the other schema
        self.assertFalse(hasattr(self.other.foo, 'baz'))

    def test_merge_inherited(self):
        """Test inherited schema overrides attributes as expected."""
        class SchemaA(Schema):
            class foo(Section):
                bar = IntOption()

            bar = IntOption()

        class SchemaB(SchemaA):
            class foo(SchemaA.foo):
                baz = IntOption()

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


class TestStringOption(unittest.TestCase):
    cls = StringOption

    def setUp(self):
        self.opt = self.cls()

    def test_init_no_args(self):
        """Test null attribute for StringOption."""
        self.assertFalse(self.opt.null)

    def test_init_null(self):
        """Test null attribute for null StringOption."""
        opt = self.cls(null=True)
        self.assertTrue(opt.null)

    def test_parse_ascii_string(self):
        """Test StringOption parse an ascii string."""
        value = self.opt.parse('42')
        self.assertEqual(value, '42')

    def test_parse_empty_string(self):
        """Test StringOption parse an empty string."""
        value = self.opt.parse('')
        self.assertEqual(value, '')

    def test_parse_null_string(self):
        """Test StringOption parse a null string."""
        opt = self.cls(null=True)
        value = opt.parse(None)
        self.assertEqual(value, None)

    def test_None_string(self):
        """Test StringOption parse the 'None' string."""
        value = self.opt.parse('None')
        self.assertEqual(value, 'None')

    def test_parse_nonascii_string(self):
        """Test StringOption parse a non-ascii string."""
        value = self.opt.parse('foóbâr')
        self.assertEqual(value, 'foóbâr')

    def test_parse_int(self):
        """Test StringOption parse an integer."""
        value = self.opt.parse(42)
        self.assertEqual(value, '42')

    def test_parse_bool(self):
        """Test StringOption parse a boolean."""
        value = self.opt.parse(False)
        self.assertEqual(value, 'False')

    def test_default(self):
        """Test default value for StringOption."""
        self.assertEqual(self.opt.default, '')

    def test_default_null(self):
        """Test default value for null StringOption."""
        opt = self.cls(null=True)
        self.assertEqual(opt.default, None)

    def test_validate_string(self):
        """Test OptionString validate a string value."""
        self.assertEqual(self.opt.validate(''), True)

    def test_validate_nonstring(self):
        """Test OptionString validate a non-string value."""
        self.assertEqual(self.opt.validate(0), False)

    def test_validate_null_string(self):
        """Test OptionString validate a null string."""
        opt = StringOption(null=True)
        self.assertEqual(opt.validate(None), True)

    def test_to_string_for_null_string(self):
        """Test OptionString to_string for a null string."""
        opt = StringOption(null=True)
        self.assertEqual(opt.to_string(None), 'None')
        self.assertEqual(opt.to_string(''), '')
        self.assertEqual(opt.to_string('foo'), 'foo')

    def test_to_string_for_non_null_string(self):
        """Test OptionString to_string for non-null string."""
        self.assertEqual(self.opt.to_string(None), None)
        self.assertEqual(self.opt.to_string(''), '')
        self.assertEqual(self.opt.to_string('foo'), 'foo')

    def test_short_name(self):
        """Test StringOption short name."""
        opt = self.cls(short_name='f')
        self.assertEqual(opt.short_name, 'f')

    def test_equal(self):
        """Test StringOption equality."""
        option1 = StringOption()
        option2 = StringOption(null=True)

        self.assertEqual(option1, option1)
        self.assertNotEqual(option1, option2)


class TestIntOption(unittest.TestCase):
    cls = IntOption

    def test_parse_int(self):
        """Test IntOption parse an integer."""
        class MySchema(Schema):
            foo = self.cls()

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
        """Test IntOption default value."""
        opt = self.cls()
        self.assertEqual(opt.default, 0)

    def test_validate_int(self):
        """Test IntOption validate an integer value."""
        opt = self.cls()
        self.assertEqual(opt.validate(0), True)

    def test_validate_nonint(self):
        """Test IntOption validate a non-integer value."""
        opt = self.cls()
        self.assertEqual(opt.validate(''), False)

    def test_short_name(self):
        """Test IntOption short name."""
        opt = self.cls(short_name='f')
        self.assertEqual(opt.short_name, 'f')


class TestBoolOption(unittest.TestCase):
    cls = BoolOption

    def test_parse_bool(self):
        """Test BoolOption parse a boolean value."""
        class MySchema(Schema):
            foo = self.cls()

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
        """Test BoolOption default value."""
        opt = self.cls()
        self.assertEqual(opt.default, False)

    def test_validate_bool(self):
        """Test BoolOption validate a boolean value."""
        opt = self.cls()
        self.assertEqual(opt.validate(False), True)

    def test_validate_nonbool(self):
        """Test BoolOption value a non-boolean value."""
        opt = self.cls()
        self.assertEqual(opt.validate(''), False)

    def test_short_name(self):
        """Test BoolOption short name."""
        opt = self.cls(short_name='f')
        self.assertEqual(opt.short_name, 'f')


class TestListOption(unittest.TestCase):
    cls = ListOption

    def test_parse_int_lines(self):
        """Test ListOption parse a list of integers."""
        class MySchema(Schema):
            foo = self.cls(item=IntOption())

        config = StringIO("[__main__]\nfoo = 42\n 43\n 44")
        expected_values = {'__main__': {'foo': [42, 43, 44]}}
        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_no_json(self):
        class MySchema(Schema):
            foo = self.cls(item=IntOption(), parse_json=False)

        config = StringIO("[__main__]\nfoo = 42\n 43\n 44")
        expected_values = {'__main__': {'foo': [42, 43, 44]}}
        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_no_json_with_json(self):
        class MySchema(Schema):
            foo = self.cls(item=IntOption(), parse_json=False)

        config = StringIO("[__main__]\nfoo = [42, 43, 44]")
        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertRaises(ValueError, parser.values)

    def test_parse_json(self):
        class MySchema(Schema):
            foo = self.cls(item=IntOption())

        config = StringIO("[__main__]\nfoo = [42, 43, 44]")
        expected_values = {'__main__': {'foo': [42, 43, 44]}}
        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_invalid_json(self):
        class MySchema(Schema):
            foo = self.cls(item=IntOption())

        config = StringIO('[__main__]\nfoo = 1, 2, 3')
        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertRaises(ValueError, parser.values)

    def test_parse_non_list_json(self):
        class MySchema(Schema):
            foo = self.cls(item=IntOption())

        config = StringIO('[__main__]\nfoo = {"foo": "bar"}')
        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertRaises(ValueError, parser.values)

    def test_parse_bool_lines(self):
        """Test ListOption parse a list of booleans."""
        class MySchema(Schema):
            foo = self.cls(item=BoolOption())

        schema = MySchema()
        config = StringIO("[__main__]\nfoo = tRuE\n No\n 0\n 1")
        expected_values = {'__main__': {'foo': [True, False, False, True]}}
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEqual(expected_values, parser.values())

    def test_parse_bool_empty_lines(self):
        """Test ListOption parse an empty list of booleans."""
        class MySchema(Schema):
            foo = self.cls(item=BoolOption())

        schema = MySchema()
        config = StringIO("[__main__]\nfoo =")
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        expected_values = {'__main__': {'foo': []}}
        self.assertEqual(expected_values, parser.values())

    def test_parse_bool_invalid_lines(self):
        """Test ListOption parse an invalid list of booleans."""
        class MySchema(Schema):
            foo = self.cls(item=BoolOption())

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
        """Test ListOption default value."""
        opt = self.cls(item=IntOption())
        self.assertEqual(opt.default, [])

    def test_remove_duplicates(self):
        """Test ListOption with remove_duplicates."""
        class MySchema(Schema):
            foo = self.cls(item=StringOption(), remove_duplicates=True)

        schema = MySchema()
        config = StringIO("[__main__]\nfoo = bla\n blah\n bla")
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEquals({'__main__': {'foo': ['bla', 'blah']}},
                          parser.values())

    def test_remove_dict_duplicates(self):
        """Test ListOption remove_duplicates with DictOption."""
        class MyOtherSchema(Schema):
            foo = self.cls(item=DictOption(), remove_duplicates=True)

        schema = MyOtherSchema()
        config = StringIO("[__main__]\nfoo = bla\n bla\n[bla]\nbar = baz")
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEquals({'__main__': {'foo': [{'bar': 'baz'}]}},
                          parser.values())

    def test_validate_list(self):
        """Test ListOption validate a list value."""
        opt = self.cls(item=IntOption())
        self.assertEqual(opt.validate([]), True)

    def test_validate_nonlist(self):
        """Test ListOption validate a non-list value."""
        opt = self.cls(item=IntOption())
        self.assertEqual(opt.validate(''), False)

    def test_default_item(self):
        """Test ListOption default item."""
        opt = self.cls()
        self.assertEqual(opt.item, StringOption())

    def test_short_name(self):
        """Test ListOption short name."""
        opt = self.cls(short_name='f')
        self.assertEqual(opt.short_name, 'f')

    def test_equal(self):
        """Test ListOption equality."""
        option1 = ListOption()
        option2 = ListOption(name='foo')
        option3 = ListOption(item=StringOption())
        option4 = ListOption(item=DictOption())
        option5 = ListOption(raw=True)
        option6 = ListOption(remove_duplicates=True)
        option7 = ListOption(raw=False, item=StringOption(raw=True))

        self.assertEqual(option1, option1)
        self.assertNotEqual(option1, option2)
        self.assertEqual(option1, option3)
        self.assertNotEqual(option1, option4)
        self.assertNotEqual(option1, option5)
        self.assertNotEqual(option1, option6)
        self.assertNotEqual(option1, option7)

    def test_to_string_when_json(self):
        option = ListOption()
        result = option.to_string(['1', '2', '3'])
        self.assertEqual(result, '["1", "2", "3"]')
        self.assertNotEqual(result, "['1', '2', '3']")

    def test_to_string_when_no_json(self):
        option = ListOption(parse_json=False)
        result = option.to_string(['1', '2', '3'])
        self.assertEqual(result, "['1', '2', '3']")


class TestTupleOption(unittest.TestCase):
    cls = TupleOption

    def test_init(self):
        """Test TupleOption constructor."""
        opt = self.cls(length=2)
        self.assertEqual(opt.length, 2)

    def test_init_no_length(self):
        """Test TupleOption default attribute values."""
        opt = self.cls()
        self.assertEqual(opt.length, 0)
        self.assertEqual(opt.default, ())

    def test_parse_no_length(self):
        """Test TupleOption parse without length."""
        class MySchema(Schema):
            foo = self.cls()

        config = StringIO('[__main__]\nfoo=1,2,3,4')
        expected_values = {'__main__': {'foo': ('1', '2', '3', '4')}}
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_tuple(self):
        """Test TupleOption parse with length."""
        class MySchema(Schema):
            foo = self.cls(length=4)

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
        """Test TupleOption default value."""
        opt = self.cls(length=2)
        self.assertEqual(opt.default, ())

    def test_validate_tuple(self):
        """Test TupleOption validate a tuple value."""
        opt = self.cls(length=2)
        self.assertEqual(opt.validate(()), True)

    def test_validate_nontuple(self):
        """Test TupleOption validate a non-tuple value."""
        opt = self.cls(length=2)
        self.assertEqual(opt.validate(0), False)

    def test_short_name(self):
        """Test TupleOption short name."""
        opt = self.cls(short_name='f')
        self.assertEqual(opt.short_name, 'f')

    def test_equal(self):
        """Test TupleOption equality."""
        option1 = TupleOption()
        option2 = TupleOption(length=2)

        self.assertEqual(option1, option1)
        self.assertNotEqual(option1, option2)


class TestDictOption(unittest.TestCase):
    cls = DictOption

    def test_init(self):
        """Test default values for DictOption attributes."""
        opt = self.cls()
        self.assertEqual(opt.spec, {})
        self.assertEqual(opt.strict, False)

        spec = {'a': IntOption(), 'b': BoolOption()}
        opt = self.cls(spec=spec)
        self.assertEqual(opt.spec, spec)
        self.assertEqual(opt.strict, False)

        opt = self.cls(spec=spec, strict=True)
        self.assertEqual(opt.spec, spec)
        self.assertEqual(opt.strict, True)

    def test_get_extra_sections(self):
        """Test DictOption get_extra_sections."""
        class MySchema(Schema):
            foo = self.cls(item=self.cls())

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

        opt = self.cls(item=self.cls())
        extra = opt.get_extra_sections('dict1', parser)
        self.assertEqual(extra, expected)

    def test_parse_dict(self):
        """Test DictOption parse a dict."""
        class MySchema(Schema):
            foo = self.cls(spec={
                'bar': StringOption(),
                'baz': IntOption(),
                'bla': BoolOption(),
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
                'foo': {'bar': 'baz', 'baz': 42, 'bla': True}}}

        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_dict_no_json(self):
        """Test DictOption parse a dict when json is disabled."""
        class MySchema(Schema):
            foo = self.cls(spec={
                'bar': StringOption(),
                'baz': IntOption(),
                'bla': BoolOption(),
            }, parse_json=False)

        config = StringIO("""[__main__]
foo = mydict
[mydict]
bar=baz
baz=42
bla=Yes
""")
        expected_values = {
            '__main__': {
                'foo': {'bar': 'baz', 'baz': 42, 'bla': True}}}

        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_dict_json(self):
        """Test DictOption parse a json dict."""
        class MySchema(Schema):
            foo = self.cls(spec={
                'bar': StringOption(),
                'baz': IntOption(),
                'bla': BoolOption(),
            })

        config = StringIO(textwrap.dedent("""
            [__main__]
            foo = {
                "bar": "baz",
                "baz": "42",
                "bla": "Yes"}
            """))
        expected_values = {
            '__main__': {
                'foo': {'bar': 'baz', 'baz': 42, 'bla': True}}}

        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_dict_json_invalid_json(self):
        """Test DictOption parse invalid json."""
        class MySchema(Schema):
            foo = self.cls(spec={
                'bar': StringOption(),
                'baz': IntOption(),
                'bla': BoolOption(),
            })

        config = StringIO(textwrap.dedent("""
            [__main__]
            foo = {'bar': 23}
            """))

        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertRaises(NoSectionError, parser.values)

    def test_parse_dict_json_non_dict_json(self):
        """Test DictOption parse json not representing a dict."""
        class MySchema(Schema):
            foo = self.cls(spec={
                'bar': StringOption(),
                'baz': IntOption(),
                'bla': BoolOption(),
            })

        config = StringIO(textwrap.dedent("""
            [__main__]
            foo = [1, 2, 3]
            """))

        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertRaises(NoSectionError, parser.values)

    def test_parse_dict_no_json_with_json(self):
        """Test DictOption parse json when json is disabled."""
        class MySchema(Schema):
            foo = self.cls(spec={
                'bar': StringOption(),
                'baz': IntOption(),
                'bla': BoolOption(),
            }, parse_json=False)

        config = StringIO(textwrap.dedent("""
            [__main__]
            foo = {
                "bar": "baz",
                "baz": "42",
                "bla": "Yes"}
            """))

        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        self.assertRaises(NoSectionError, parser.values)

    def test_parse_raw(self):
        """Test DictOption parse using raw=True."""
        class MySchema(Schema):
            foo = self.cls(spec={
                'bar': StringOption(),
                'baz': IntOption(),
                'bla': BoolOption(),
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

    def test_parse_json_raw_with_interpolation_marks(self):
        """Test DictOption parse json using raw=True when data has interpolation marks."""
        class MySchema(Schema):
            class logging(Section):
                formatters = self.cls(raw=True, item=self.cls())

        config = StringIO(textwrap.dedent("""
            [logging]
            formatters = {"sample": {"format": "%(name)s"}}
            """))
        expected = {'sample': {'format': '%(name)s'}}

        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        parsed = parser.values('logging')['formatters']
        self.assertEqual(parsed, expected)

    def test_parse_no_json_raw_with_interpolation_marks(self):
        """Test DictOption parse non-json using raw=True when data has interpolation marks."""
        class MySchema(Schema):
            class logging(Section):
                formatters = self.cls(raw=True, item=self.cls())

        config = StringIO(textwrap.dedent("""
            [logging]
            formatters = logging_formatters

            [logging_formatters]
            sample = sample_formatter

            [sample_formatter]
            format = %%(name)s
            """))
        expected = {'sample': {'format': '%(name)s'}}

        schema = MySchema()
        parser = SchemaConfigParser(schema)
        parser.readfp(config)
        parsed = parser.values('logging')['formatters']
        self.assertEqual(parsed, expected)

    def test_parse_invalid_key_in_parsed(self):
        """Test DictOption parse with an invalid key in the config."""
        class MySchema(Schema):
            foo = self.cls(spec={'bar': IntOption()})

        config = StringIO("[__main__]\nfoo=mydict\n[mydict]\nbaz=2")
        expected_values = {'__main__': {'foo': {'bar': 0, 'baz': '2'}}}
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_invalid_key_in_spec(self):
        """Test DictOption parse with an invalid key in the spec."""
        class MySchema(Schema):
            foo = self.cls(spec={
                'bar': IntOption(),
                'baz': IntOption(fatal=True)})

        config = StringIO("[__main__]\nfoo=mydict\n[mydict]\nbar=2")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertRaises(ValueError, parser.parse_all)

    def test_default(self):
        opt = self.cls(spec={})
        self.assertEqual(opt.default, {})

    def test_parse_no_strict_missing_args(self):
        """Test DictOption parse a missing key in non-strict mode."""
        class MySchema(Schema):
            foo = self.cls(spec={'bar': IntOption()})

        config = StringIO("[__main__]\nfoo=mydict\n[mydict]")
        expected_values = {'__main__': {'foo': {'bar': 0}}}
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_no_strict_extra_args(self):
        class MySchema(Schema):
            foo = self.cls()

        config = StringIO("[__main__]\nfoo=mydict\n[mydict]\nbar=2")
        expected_values = {'__main__': {'foo': {'bar': '2'}}}
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_no_strict_with_item(self):
        """Test DictOption parse in non-strict mode with an item spec."""
        class MySchema(Schema):
            foo = self.cls(
                      item=self.cls(
                          item=IntOption()))
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
        """Test DictOption parse in strict mode."""
        class MySchema(Schema):
            spec = {'bar': IntOption()}
            foo = self.cls(spec=spec, strict=True)

        config = StringIO("[__main__]\nfoo=mydict\n[mydict]\nbar=2")
        expected_values = {'__main__': {'foo': {'bar': 2}}}
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_strict_missing_vars(self):
        """Test DictOption parse in strict mode with missing values."""
        class MySchema(Schema):
            spec = {'bar': IntOption(),
                    'baz': IntOption()}
            foo = self.cls(spec=spec, strict=True)

        config = StringIO("[__main__]\nfoo=mydict\n[mydict]\nbar=2")
        expected_values = {'__main__': {'foo': {'bar': 2, 'baz': 0}}}
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertEqual(parser.values(), expected_values)

    def test_parse_strict_extra_vars(self):
        """Test DictOption parse in strict mode with extra values."""
        class MySchema(Schema):
            spec = {'bar': IntOption()}
            foo = self.cls(spec=spec, strict=True)

        config = StringIO("[__main__]\nfoo=mydict\n[mydict]\nbar=2\nbaz=3")
        parser = SchemaConfigParser(MySchema())
        parser.readfp(config)
        self.assertRaises(ValueError, parser.parse_all)

    def test_validate_dict(self):
        opt = self.cls()
        self.assertEqual(opt.validate({}), True)

    def test_validate_nondict(self):
        opt = self.cls()
        self.assertEqual(opt.validate(0), False)

    def test_short_name(self):
        """Test DictOption short name."""
        opt = self.cls(short_name='f')
        self.assertEqual(opt.short_name, 'f')

    def test_equal(self):
        """Test DictOption equality."""
        option1 = DictOption()
        option2 = DictOption(spec={'foo': BoolOption()})
        option3 = DictOption(strict=True)
        option4 = DictOption(item=StringOption())
        option5 = DictOption(item=IntOption())

        self.assertEqual(option1, option1)
        self.assertNotEqual(option1, option2)
        self.assertNotEqual(option1, option3)
        self.assertEqual(option1, option4)
        self.assertNotEqual(option1, option5)

    def test_to_string_when_json(self):
        option = DictOption()
        result = option.to_string({'foo': '1'})
        self.assertEqual(result, '{"foo": "1"}')

    def test_to_string_when_no_json(self):
        option = DictOption(parse_json=False)
        result = option.to_string({'foo': '1'})
        self.assertEqual(result, str({'foo': '1'}))


class TestListOfDictOption(unittest.TestCase):
    def test_parse_lines_of_dict(self):
        """Test ListOption parse a list of dicts."""
        class MySchema(Schema):
            foo = ListOption(item=DictOption(
                spec={
                    'bar': StringOption(),
                    'baz': IntOption(),
                    'bla': BoolOption(),
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
    """Test DictOption parse dict items."""
    def test_parse_dict_with_dicts(self):
        innerspec = {'bar': StringOption(),
                     'baz': IntOption(),
                     'bla': BoolOption(),
                    }
        spec = {'name': StringOption(),
                'size': IntOption(),
                'options': DictOption(spec=innerspec)}

        class MySchema(Schema):
            foo = DictOption(spec=spec)

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
            foo = ListOption(item=TupleOption(length=3))

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


class TestSection(unittest.TestCase):
    cls = Section

    def test_default_name(self):
        """Test Section default name."""
        section = self.cls()
        self.assertEqual(section.name, '')

    def test_custom_name(self):
        """Test Section custom name."""
        section = self.cls(name='foo')
        self.assertEqual(section.name, 'foo')

    def test_equality(self):
        """Test Section equality."""
        section1 = self.cls()
        section2 = self.cls()
        section3 = self.cls(name='foo')
        section4 = self.cls()
        section4.foo = IntOption()

        self.assertEqual(section1, section1)
        self.assertEqual(section1, section2)
        self.assertNotEqual(section1, section3)
        self.assertNotEqual(section1, section4)

    def test_repr(self):
        """Test Section repr."""
        section1 = self.cls()
        section2 = self.cls(name='foo')

        self.assertEqual(repr(section1), '<{0}>'.format(self.cls.__name__))
        self.assertEqual(repr(section2),
            '<{0} foo>'.format(self.cls.__name__))

    def test_has_option(self):
        """Test Section has_option method."""
        section = self.cls()
        section.foo = IntOption()
        section.bar = 4

        self.assertEqual(section.has_option('foo'), True)
        self.assertEqual(section.has_option('bar'), False)

    def test_option(self):
        """Test Section option method."""
        section = self.cls()
        section.foo = IntOption()

        self.assertEqual(section.option('foo'), section.foo)
        self.assertRaises(NoOptionError, section.option, 'bar')

    def test_options(self):
        """Test Section options method."""
        section = self.cls()
        section.foo = IntOption()
        section.bar = 4

        self.assertEqual(section.options(), [section.foo])


class MultiSchemaTestCase(unittest.TestCase):
    def test_merge_schemas_no_conflicts(self):
        class SchemaA(Schema):
            foo = IntOption()

        class SchemaB(Schema):
            bar = BoolOption()

        schema = merge(SchemaA, SchemaB)()
        self.assertEqual(set(s.name for s in schema.sections()),
            set(['__main__']))
        self.assertEqual(set(o.name for o in schema.options('__main__')),
            set(['foo', 'bar']))
        self.assertEqual(schema.foo, SchemaA().foo)
        self.assertEqual(schema.bar, SchemaB().bar)

    def test_merge_schemas_same_section(self):
        class SchemaA(Schema):
            class foo(Section):
                bar = IntOption()

        class SchemaB(Schema):
            class foo(Section):
                baz = BoolOption()

        schema = merge(SchemaA, SchemaB)()
        self.assertEqual(set(s.name for s in schema.sections()),
            set(['foo']))
        self.assertEqual(set(o.name for o in schema.options('foo')),
            set(['bar', 'baz']))
        self.assertEqual(schema.foo.bar, SchemaA().foo.bar)
        self.assertEqual(schema.foo.baz, SchemaB().foo.baz)

    def test_merge_schemas_duplicate(self):
        class SchemaA(Schema):
            foo = IntOption()

        class SchemaB(Schema):
            foo = IntOption()

        schema = merge(SchemaA, SchemaB)()
        self.assertEqual(set(s.name for s in schema.sections()),
            set(['__main__']))
        self.assertEqual(set(o.name for o in schema.options('__main__')),
            set(['foo']))
        self.assertEqual(schema.foo, SchemaA().foo)
        self.assertEqual(schema.foo, SchemaB().foo)

    def test_merge_schemas_conflicts(self):
        class SchemaA(Schema):
            foo = IntOption()

        class SchemaB(Schema):
            foo = BoolOption()

        try:
            merge(SchemaA, SchemaB)
            self.fail('SchemaValidationError not raised.')
        except SchemaValidationError, e:
            self.assertEqual(str(e),
                "Conflicting option '__main__.foo' while merging schemas.")
