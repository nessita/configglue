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

import __builtin__
import sys
from optparse import OptionParser
from collections import namedtuple

from configglue.inischema import (
    parsers,
    AttributedConfigParser,
)
from configglue.pyschema.parser import SchemaConfigParser
from configglue.pyschema.schema import (
    BoolConfigOption,
    ConfigSection,
    IntConfigOption,
    LinesConfigOption,
    Schema,
    StringConfigOption,
)


__all__ = [
    'configglue',
    'ini2schema',
    'schemaconfigglue',
]

SchemaGlue = namedtuple("SchemaGlue", "schema_parser option_parser options args")
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

    parser2option = {'unicode': StringConfigOption,
                     'int': IntConfigOption,
                     'bool': BoolConfigOption,
                     'lines': LinesConfigOption}

    class MySchema(Schema):
        pass

    for section_name in p.sections():
        if section_name == '__main__':
            section = MySchema
        else:
            section = ConfigSection()
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

            attrs = {}
            option_help = option.attrs.pop('help', None)
            if option_help is not None:
                attrs['help'] = option_help
            if not option.is_empty:
                attrs['default'] = parser_fun(option.value, *parser_args)
            option_action = option.attrs.pop('action', None)
            if option_action is not None:
                attrs['action'] = option_action

            klass = parser2option.get(parser, StringConfigOption)
            if parser == 'lines':
                instance = klass(StringConfigOption(), **attrs)
            else:
                instance = klass(**attrs)
            setattr(section, option_name, instance)

    return SchemaConfigParser(MySchema())


def schemaconfigglue(parser, op=None, argv=None):
    """Populate an OptionParser with options and defaults taken from a
    fully loaded SchemaConfigParser.
    """

    def long_name(option):
        if option.section.name == '__main__':
            return option.name
        return option.section.name + '_' + option.name

    def opt_name(option):
        return long_name(option).replace('-', '_')

    if op is None:
        op = OptionParser()
    if argv is None:
        argv = sys.argv[1:]
    schema = parser.schema

    for section in schema.sections():
        if section.name == '__main__':
            og = op
        else:
            og = op.add_option_group(section.name)
        for option in section.options():
            kwargs = {}
            if option.help:
                kwargs['help'] = option.help
            kwargs['default'] = parser.get(section.name, option.name)
            kwargs['action'] = option.action
            og.add_option('--' + long_name(option), **kwargs)
    options, args = op.parse_args(argv)

    for section in schema.sections():
        for option in section.options():
            value = getattr(options, opt_name(option))
            if parser.get(section.name, option.name) != value:
                # the value has been overridden by an argument;
                # update it.
                parser.set(section.name, option.name, value)

    return IniGlue(op, options, args)


def configglue(schema_class, configs, usage=None):
    scp = SchemaConfigParser(schema_class())
    scp.read(configs)
    if usage is not None:
        op = OptionParser(usage=usage)
    else:
        op = None
    parser, opts, args = schemaconfigglue(scp, op=op)
    is_valid, reasons = scp.is_valid(report=True)
    if not is_valid:
        parser.error(reasons[0])
    return SchemaGlue(scp, parser, opts, args)

