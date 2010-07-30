# This file is part of configglue, by John R. Lenton <john.lenton@canonical.com>
# (C) 2009 by Canonical Ltd.
# Released under the BSD License (see the file LICENSE)
# For bug reports, support, and new releases: http://launchpad.net/configglue

# in testfiles, putting docstrings on methods messes up with the
# runner's output, so pylint: disable-msg=C0111

import unittest

from configglue.inischema import parsers

class TestParsers(unittest.TestCase):
    def test_bool(self):
        for value in ('true', '1', 'on', 'yes',
                      'True', 'YES', 'oN'):
            self.assertEqual(parsers.bool_parser(value), True)
        for value in ('false', '0', 'off', 'no',
                      'faLSE', 'No', 'oFf'):
            self.assertEqual(parsers.bool_parser(value), False)
        for value in ('xyzzy', '', '-1', '0.', '0.1'):
            self.assertRaises(ValueError, parsers.bool_parser, value)

    def test_lines(self):
        self.assertEqual(parsers.lines('abc\ndef'), ['abc', 'def'])
