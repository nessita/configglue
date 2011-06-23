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

import os
import sys
from ConfigParser import (
    NoOptionError,
    NoSectionError,
)
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
            if not option.fatal:
                kwargs['default'] = parser.get(section.name, option.name)
            kwargs['action'] = option.action
            og.add_option('--' + long_name(option), **kwargs)
    options, args = op.parse_args(argv)

    def set_value(section, option, value):
        # if value is not of the right type, cast it
        if not option.validate(value):
            value = option.parse(value)
        parser.set(section.name, option.name, value)

    for section in schema.sections():
        for option in section.options():
            # 1. op value != parser value
            # 2. op value == parser value != env value
            # 3. op value == parser value == env value or not env value

            op_value = getattr(options, opt_name(option))
            try:
                parser_value = parser.get(section.name, option.name)
            except (NoSectionError, NoOptionError):
                parser_value = None
            env_value = os.environ.get("CONFIGGLUE_{0}".format(
                long_name(option).upper()))

            if op_value != parser_value:
                set_value(section, option, op_value)
            elif env_value is not None and env_value != parser_value:
                set_value(section, option, env_value)

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
        parser.error('\n'.join(reasons))
    return SchemaGlue(scp, parser, opts, args)
