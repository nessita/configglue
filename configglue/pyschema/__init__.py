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
from optparse import OptionParser
import sys

# XXX: more imports at bottom (we probably want to fix this)

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

    parser2option = {'unicode': options.StringConfigOption,
                     'int': options.IntConfigOption,
                     'bool': options.BoolConfigOption,
                     'lines': options.LinesConfigOption}

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

            klass = parser2option.get(parser, options.StringConfigOption)
            if parser == 'lines':
                instance = klass(options.StringConfigOption(), **attrs)
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

    return op, options, args

def super_vars(obj):
    """An extended version of vars() that walks all base classes."""
    items = {}
    if hasattr(obj, '__mro__'):
        bases = map(vars, obj.__mro__)
        map(items.update, bases)
    else:
        items = vars(obj)
    return items

NO_DEFAULT = object()


class ConfigOption(object):
    """Base class for Config Options.

    ConfigOptions are never bound to a particular conguration file, and
    simply describe one particular available option.

    They also know how to parse() the content of a config file in to the right
    type of object.

    If self.raw == True, then variable interpolation will not be carried out
    for this config option.

    If self.require_parser == True, then the parse() method will have a second
    argument, parser, that should receive the whole SchemaConfigParser to
    do the parsing.  This is needed for config options that need to look at
    other parts of the config file to be able to carry out their parsing,
    like DictConfigOptions.

    If self.fatal == True, SchemaConfigParser's parse_all will raise an
    exception if no value for this option is provided in the configuration
    file.  Otherwise, the self.default value will be used if the option is
    omitted.

    In runtime, after instantiating the Schema, each ConfigOption will also
    know its own name and to which section it belongs.
    """

    require_parser = False

    def __init__(self, name='', raw=False, default=NO_DEFAULT, fatal=False, help='',
                 section=None, action='store'):
        self.name = name
        self.raw = raw
        self.fatal = fatal
        if default is NO_DEFAULT:
            default = self._get_default()
        self.default = default
        self.help = help
        self.section = section
        self.action = action

    def __eq__(self, other):
        try:
            equal = (self.name == other.name and
                     self.raw == other.raw and
                     self.fatal == other.fatal and
                     self.default == other.default and
                     self.help == other.help)
            if self.section is not None and other.section is not None:
                # only test for section name to avoid recursion
                equal &= self.section.name == other.section.name
            else:
                equal &= (self.section is None and other.section is None)
        except AttributeError:
            equal = False

        return equal

    def __repr__(self):
        extra = ' raw' if self.raw else ''
        extra += ' fatal' if self.fatal else ''
        section = self.section.name if self.section is not None else None
        if section is not None:
            name = " %s.%s" % (section, self.name)
        elif self.name:
            name = " %s" % self.name
        else:
            name = ''
        value = "<ConfigOption%s%s>" % (name, extra)
        return value

    def _get_default(self):
        return None

    def parse(self, value):
        raise NotImplementedError()


class ConfigSection(object):
    """A group of options.

    This class is just a bag you can dump ConfigOptions in.

    After instantiating the Schema, each ConfigSection will know its own
    name.
    """
    def __init__(self, name=''):
        self.name = name

    def __eq__(self, other):
        return (self.name == other.name and
                self.options() == other.options())

    def __repr__(self):
        if self.name:
            name = " %s" % self.name
        else:
            name = ''
        value = "<ConfigSection%s>" % name
        return value

    def has_option(self, name):
        """Return True if a ConfigOption with the given name is available"""
        opt = getattr(self, name, None)
        return isinstance(opt, ConfigOption)

    def option(self, name):
        """Return a ConfigOption by name"""
        opt = getattr(self, name, None)
        assert opt is not None, "Invalid ConfigOption name '%s'" % name
        return opt

    def options(self):
        """Return a list of all available ConfigOptions within this section"""
        return [getattr(self, att) for att in vars(self)
                if isinstance(getattr(self, att), ConfigOption)]


# usability tweak -- put everything in the base namespace to make import lines
# shorter
from options import (BoolConfigOption, DictConfigOption, IntConfigOption,
    LinesConfigOption, StringConfigOption, TupleConfigOption)
from parser import SchemaConfigParser
from schema import Schema

# circular import avoidance
from configglue.inischema import AttributedConfigParser, parsers
