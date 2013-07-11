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

""" TypedConfigParser lives here """
from __future__ import absolute_import, unicode_literals

import os

from configglue._compat import text_type
from . import parsers
from .attributed import AttributedConfigParser


class TypedConfigParser(AttributedConfigParser):
    """Building on AttributedConfigParser, handle the idea of having a
    configuration file that knows what type its options are.
    """
    def __init__(self, *args, **kwargs):
        super(TypedConfigParser, self).__init__(*args, **kwargs)
        self.parsers = {'bool': parsers.bool_parser,
                        'complex': complex,
                        'float': float,
                        'int': int,
                        'lines': parsers.lines,
                        'unicode': text_type,
                        'getenv': os.getenv,
                        None: lambda x: x}

    def add_parser(self, name, parser, clobber=False):
        """Add a custom parser

        @param name: the name with which you can ask for this parser
                     in the configuration file
        @param parser: the parser itself
        @param clobber: whether to overwite an existing parser
        """
        if name not in self.parsers or clobber:
            self.parsers[name] = parser
        else:
            raise ValueError('A parser by that name already exists')

    def add_parsers(self, *args):
        """Add multiple custom parsers

        @param args: any number of (name, parser, [clobber]) tuples
        """
        for arg in args:
            self.add_parser(*arg)

    def parse(self, section, option):
        """Parse a single option in a single section.

        This actually consumes the 'parser', 'parser_args' and 'default'
        attributes.

        @param section: the section within which to look for the option
        @param option: the 'base' option to parse
        """
        super(TypedConfigParser, self).parse(section, option)

        value = self.get(section, option)

        if 'default.parser' in value.attrs:
            parser = self.parsers[value.attrs.pop('default.parser')]
            value.attrs['default'] = parser(value.attrs['default'])

        if value.is_empty:
            if 'default' in value.attrs:
                value.value = value.attrs['default']
            else:
                value.value = None

        if 'parser' in value.attrs:
            args = value.attrs.pop('parser.args', ())
            if args != ():
                args_parser = value.attrs.pop('parser.args.parser', 'lines')
                args = self.parsers[args_parser](args)
            # leave the parser hanging around for if you need it later
            value.parser = self.parsers[value.attrs.pop('parser')]
            value.value = value.parser(value.value, *args)
        else:
            value.parser = self.parsers[None]

        # tadaa!
        self.set(section, option, value)
