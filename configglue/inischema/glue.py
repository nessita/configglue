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

"""configglue lives here
"""
from __future__ import absolute_import

import __builtin__
from collections import namedtuple

from configglue.inischema import parsers
from configglue.inischema.attributed import AttributedConfigParser
from configglue.glue import schemaconfigglue
from configglue.parser import SchemaConfigParser
from configglue.schema import (
    BoolOption,
    Section,
    IntOption,
    ListOption,
    Schema,
    StringOption,
)


__all__ = [
    'configglue',
    'ini2schema',
]


IniGlue = namedtuple("IniGlue", " option_parser options args")


def ini2schema(fd, p=None):
    """
    Turn a fd that refers to a INI-style schema definition into a
    SchemaConfigParser object

    @param fd: file-like object to read the schema from
    @param p: a parser to use. If not set, uses AttributedConfigParser
    """
    if p is None:
        p = AttributedConfigParser()
    p.readfp(fd)
    p.parse_all()

    parser2option = {'unicode': StringOption,
                     'int': IntOption,
                     'bool': BoolOption,
                     'lines': ListOption}

    class MySchema(Schema):
        pass

    for section_name in p.sections():
        if section_name == '__main__':
            section = MySchema
        else:
            section = Section(name=section_name)
            setattr(MySchema, section_name, section)
        for option_name in p.options(section_name):
            option = p.get(section_name, option_name)

            parser = option.attrs.pop('parser', 'unicode')
            parser_args = option.attrs.pop('parser.args', '').split()
            parser_fun = getattr(parsers, parser, None)
            if parser_fun is None:
                parser_fun = getattr(__builtin__, parser, None)
            if parser_fun is None:
                parser_fun = lambda x: x

            attrs = {'name': option_name}
            option_help = option.attrs.pop('help', None)
            if option_help is not None:
                attrs['help'] = option_help
            if not option.is_empty:
                attrs['default'] = parser_fun(option.value, *parser_args)
            option_action = option.attrs.pop('action', None)
            if option_action is not None:
                attrs['action'] = option_action

            klass = parser2option.get(parser, StringOption)
            if parser == 'lines':
                instance = klass(item=StringOption(), **attrs)
            else:
                instance = klass(**attrs)
            setattr(section, option_name, instance)

    return SchemaConfigParser(MySchema())


def configglue(fileobj, *filenames, **kwargs):
    args = kwargs.pop('args', None)
    parser, opts, args = schemaconfigglue(ini2schema(fileobj), argv=args)
    return IniGlue(parser, opts, args)
