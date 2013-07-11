# -*- coding: utf-8 -*-
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

import sys
import textwrap
import unittest
from io import StringIO

from configglue.inischema.glue import (
    configglue,
    ini2schema,
)
from configglue.glue import schemaconfigglue


class TestGlueConvertor(unittest.TestCase):
    def setUp(self):
        # make sure we have a clean sys.argv so as not to have unexpected test
        # results
        self.old_argv = sys.argv
        sys.argv = []

    def tearDown(self):
        # restore old sys.argv
        sys.argv = self.old_argv

    def test_empty(self):
        s = ""
        _, cg, _ = configglue(StringIO(s))
        _, sg, _ = schemaconfigglue(ini2schema(StringIO(s)))
        self.assertEqual(vars(cg), vars(sg))

    def test_simple(self):
        s = "[foo]\nbar = 42\n"
        _, cg, _ = configglue(StringIO(s))
        _, sg, _ = schemaconfigglue(ini2schema(StringIO(s)))
        self.assertEqual(vars(cg), vars(sg))

    def test_main(self):
        s = "[__main__]\nbar = 42\n"
        _, cg, _ = configglue(StringIO(s))
        _, sg, _ = schemaconfigglue(ini2schema(StringIO(s)))
        self.assertEqual(vars(cg), vars(sg))

    def test_parser_none(self):
        s = "[__main__]\nbar = meeeeh\nbar.parser = none"
        _, cg, _ = configglue(StringIO(s),
                              extra_parsers=[('none', str)])
        _, sg, _ = schemaconfigglue(ini2schema(StringIO(s)))
        self.assertEqual(vars(cg), vars(sg))

    def test_parser_unicode(self):
        s = textwrap.dedent("""
            [__main__]
            bar = zátrapa
        """)
        _, cg, _ = configglue(StringIO(s))
        _, sg, _ = schemaconfigglue(ini2schema(StringIO(s)))
        self.assertEqual(vars(cg), vars(sg))

    def test_parser_int(self):
        s = "[__main__]\nbar = 42\nbar.parser = int\n"
        _, cg, _ = configglue(StringIO(s))
        _, sg, _ = schemaconfigglue(ini2schema(StringIO(s)))
        self.assertEqual(vars(cg), vars(sg))

    def test_parser_bool(self):
        s = "[__main__]\nbar = true\nbar.parser = bool \n"
        _, cg, _ = configglue(StringIO(s))
        _, sg, _ = schemaconfigglue(ini2schema(StringIO(s)))
        self.assertEqual(vars(cg), vars(sg))

if __name__ == '__main__':
    unittest.main()
