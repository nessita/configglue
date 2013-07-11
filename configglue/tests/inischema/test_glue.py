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

import sys
import unittest
from io import BytesIO, StringIO, TextIOWrapper

from mock import patch

from configglue._compat import PY2
from configglue.inischema.glue import configglue


class TestBase(unittest.TestCase):
    """ Base class to keep common set-up """
    def setUp(self):
        self.file = TextIOWrapper(BytesIO(self.ini))
        self.old_sys_argv = sys.argv
        sys.argv = ['']

    def tearDown(self):
        sys.argv = self.old_sys_argv


class TestGlue(TestBase):
    ini = b'''
[blah]
foo.help = yadda yadda yadda
         yadda
foo.metavar = FOO
foo.parser = int
foo = 2
'''
    arg = '--blah_foo'
    opt = 'blah_foo'
    val = 2

    def test_ini_file_wins_when_no_args(self):
        parser, options, args = configglue(self.file, args=[])
        self.assertEqual(vars(options),
                         {self.opt: self.val})

    def test_args_win(self):
        parser, options, args = configglue(self.file,
                                           args=['', self.arg + '=5'])
        self.assertEqual(vars(options),
                         {self.opt: '5'})

    def test_help_is_displayed(self):
        new_callable = StringIO
        if PY2:
            new_callable = BytesIO

        with patch('sys.stdout', new_callable=new_callable) as mock_stdout:
            try:
                configglue(self.file, args=['', '--help'])
            except SystemExit:
                output = mock_stdout.getvalue()
        self.assertTrue('yadda yadda yadda yadda' in output)


class TestCrazyGlue(TestGlue):
    ini = b'''
[bl-ah]
foo.default = 3
foo.help = yadda yadda yadda
         yadda
foo.metavar = FOO
foo.parser = int
foo = 2
'''
    arg = '--bl-ah_foo'
    opt = 'bl_ah_foo'


class TestNoValue(TestGlue):
    ini = b'''
[blah]
foo.help = yadda yadda yadda
         yadda
foo.metavar = FOO
foo.parser = int
foo = 3
'''
    val = 3


class TestGlue2(TestBase):
    ini = b'[__main__]\na=1\n'

    def test_main(self):
        parser, options, args = configglue(self.file)
        self.assertEqual(options.a, '1')


class TestGlue3(TestBase):
    ini = b'[x]\na.help=hi\n'

    def test_empty(self):
        parser, options, args = configglue(self.file)
        self.assertEqual(options.x_a, '')

    def test_accepts_args_and_filenames(self):
        parser, options, args = configglue(self.file, 'dummy',
                                           args=['', '--x_a=1'])
        self.assertEqual(options.x_a, '1')


class TestGlueBool(TestBase):
    ini = b'''[__main__]
foo.parser=bool
foo.action=store_true

bar.default = True
bar.parser = bool
bar.action = store_false
'''

    def test_store_true(self):
        parser, options, args = configglue(self.file, args=['', '--foo'])
        self.assertEqual(options.foo, True)

    def test_store_false(self):
        parser, options, args = configglue(self.file, args=['', '--bar'])
        self.assertEqual(options.bar, False)


class TestGlueLines(TestBase):
    ini = b'''[__main__]
foo.parser = lines
foo.action = append

bar = a
      b
bar.parser = lines
bar.action = append
'''

    def test_nothing(self):
        parser, options, args = configglue(self.file)
        self.assertEqual(options.foo, [])

    def test_no_append(self):
        parser, options, args = configglue(self.file)
        self.assertEqual(options.bar, ['a', 'b'])

    def test_append_on_empty(self):
        parser, options, args = configglue(self.file, args=['', '--foo=x'])
        self.assertEqual(options.foo, ['x'])

    def test_append(self):
        parser, options, args = configglue(self.file, args=['', '--bar=x'])
        self.assertEqual(options.bar, ['a', 'b', 'x'])
