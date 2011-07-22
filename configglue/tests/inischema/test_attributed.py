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

# in testfiles, putting docstrings on methods messes up with the
# runner's output, so pylint: disable-msg=C0111

import unittest
from ConfigParser import RawConfigParser
from StringIO import StringIO

from configglue.inischema.attributed import AttributedConfigParser


class BaseTest(unittest.TestCase):
    """ Base class to keep common set-up """
    def setUp(self):
        self.config_string = '''
[xyzzy]
foo         = 5
foo.banana  = yellow
foo.mango   = orange
foo.noise   = white

bar.blah    = 23
'''
        self.config = AttributedConfigParser()
        self.config.readfp(StringIO(self.config_string))


class TestAttributed(BaseTest):
    """ pretty basic tests of AttributedConfigParser """
    def test_config_before_parsing_is_plain(self):
        rawConfig = RawConfigParser()
        rawConfig.readfp(StringIO(self.config_string))
        self.assertEqual([(section, sorted(self.config.items(section)))
                          for section in self.config.sections()],
                         [(section, sorted(rawConfig.items(section)))
                          for section in rawConfig.sections()])

    def test_config_after_parsing_is_attributed(self):
        self.config.parse_all()
        self.assertEqual(self.config.get('xyzzy',
                                         'foo').attrs['noise'], 'white')

    def test_config_after_parsing_still_knows_about_empty_values(self):
        self.config.parse_all()
        self.assertTrue(self.config.get('xyzzy', 'bar').is_empty)
