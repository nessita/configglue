# -*- encoding: utf-8 -*-
###############################################################################
#
# configglue -- glue for your apps' configuration
#
# A library for simple, DRY configuration of applications
#
# (C) 2009--2013 by Canonical Ltd.
# by John R. Lenton <john.lenton@canonical.com>
# and Ricardo Kirkner <ricardo.kirkner@canonical.com>
#
# Released under the BSD License (see the file LICENSE)
#
# For bug reports, support, and new releases: http://launchpad.net/configglue
#
###############################################################################
from __future__ import unicode_literals

# in testfiles, putting docstrings on methods messes up with the
# runner's output, so pylint: disable-msg=C0111

import unittest
from io import StringIO

from configglue._compat import RawConfigParser
from configglue.inischema.typed import TypedConfigParser


marker = object()


def some_parser(value):
    if value == 'marker':
        return marker
    else:
        return None


class BaseTest(unittest.TestCase):
    """ Base class to keep common set-up """
    def setUp(self):
        self.config_string = '''
[xyzzy]
foo.parser = complex
foo.default = 1j

bar.parser = int
bar.default = -1
bar = 2

baz.parser = some.parser
baz = marker

baz2.parser = more.parser
baz2 = -1

meep = árbol
meep.parser = unicode

thud.help = this is the help for thud

woof.default = marker
woof.default.parser = some.parser
woof.parser = bool
'''
        self.config = TypedConfigParser()
        self.config.readfp(StringIO(self.config_string))


class TestBackwardsCompat(BaseTest):
    """ rather basic backwards compatibility checker
    """
    def test_config_before_parse_is_plain(self):
        rawConfig = RawConfigParser()
        rawConfig.readfp(StringIO(self.config_string))
        self.assertEqual([(section, sorted(self.config.items(section)))
                          for section in self.config.sections()],
                         [(section, sorted(rawConfig.items(section)))
                          for section in rawConfig.sections()])


class TestParserd(BaseTest):
    """Test the different parsing situations"""
    def test_some_builtin_parser(self):
        self.config.parse('xyzzy', 'bar')
        self.assertEqual(self.config.get('xyzzy', 'bar').value, 2)

    def test_add_second_custom_parser_fails(self):
        self.config.add_parser('some.parser', some_parser)
        self.assertRaises(ValueError, self.config.add_parser,
                          'some.parser', some_parser)

    def test_custom_parser(self):
        self.config.add_parser('some.parser', some_parser)
        self.config.parse('xyzzy', 'baz')
        self.assertEqual(self.config.get('xyzzy', 'baz').value, marker)

    def test_value_is_default_if_empty(self):
        self.config.parse('xyzzy', 'foo')
        self.assertEqual(self.config.get('xyzzy', 'foo').value, 1j)

    def test_parse_default_parser(self):
        self.config.add_parser('some.parser', some_parser)
        self.config.parse('xyzzy', 'woof')
        self.assertTrue(self.config.get('xyzzy', 'woof').value)

    def test_parse_all_parses_all(self):
        self.config.add_parser('some.parser', some_parser)
        self.config.add_parser('more.parser', some_parser)
        self.config.parse_all()
        self.assertEqual([(section, [(k, v.value) for (k, v) in
                                     sorted(self.config.items(section))])
                          for section in self.config.sections()],
                         [('xyzzy', [('bar', 2),
                                     ('baz', marker),
                                     ('baz2', None),
                                     ('foo', 1j),
                                     ('meep', '\xe1rbol'),
                                     ('thud', None),
                                     ('woof', True),
                                     ])])

    def test_add_multiple_parsers(self):
        self.config.add_parsers(('some.parser', some_parser),
                                ('more.parser', some_parser))
        self.config.parse('xyzzy', 'baz')
        self.config.parse('xyzzy', 'baz2')
        self.assertEqual(self.config.get('xyzzy', 'baz').value, marker)
        self.assertEqual(self.config.get('xyzzy', 'baz2').value, None)

    def test_add_mutliple_with_repeat_without_clobber(self):
        self.assertRaises(ValueError,
                          self.config.add_parsers,
                          ('some.parser', some_parser),
                          ('some.parser', some_parser))

    def test_add_multiple_with_repeat_with_clobber(self):
        self.config.add_parsers(('some.parser', some_parser),
                                ('some.parser', bool, True))
        self.config.parse('xyzzy', 'baz')
        self.assertEqual(self.config.get('xyzzy', 'baz').value, True)


if __name__ == '__main__':
    unittest.main()
