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

import sys
from optparse import OptionParser
from collections import namedtuple

from configglue.pyschema.parser import SchemaConfigParser


__all__ = [
    'configglue',
    'schemaconfigglue',
]


SchemaGlue = namedtuple("SchemaGlue",
    "schema_parser option_parser options args")


def schemaconfigglue(parser, op=None, argv=None):
    """Glue an OptionParser with a SchemaConfigParser.

    The OptionParser is populated with options and defaults taken from the
    SchemaConfigParser.

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
                # the value has been overridden by an argument
                if isinstance(value, basestring):
                    # parse it to the right type if it's a string
                    value = option.parse(value)
                parser.set(section.name, option.name, value)

    return op, options, args


def configglue(schema_class, configs, usage=None):
    """Parse configuration files using a provided schema.

    The standard workflow for configglue is to instantiate a schema class,
    feed it with some config files, and validate the parser state afterwards.
    This utility function executes this standard worfklow so you don't have
    to repeat yourself.

    """
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
