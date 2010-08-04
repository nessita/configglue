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

"""configglue lives here
"""
from __future__ import absolute_import

from .typed import TypedConfigParser
from optparse import OptionParser

__all__ = ('configglue',)

def normoptname(parser, section, option):
    """Helper that handles the special __main__ section for option names"""
    if section == '__main__':
        return parser.optionxform(option)
    else:
        return parser.optionxform(section +'-'+ option)
    

def configglue(fileobj, *filenames, **kwargs):
    """Populate an OptionParser with options and defaults taken from a
    series of files.

    @param fileobj: An INI file, as a file-like object.
    @param filenames: An optional series of filenames to merge.
    @param kwargs: options passed on to the OptionParser constructor except for:
    @param args: parse these args (defaults to sys.argv[1:])
    @param extra_parsers: list of (name, parser) parser tuples to add to the 
                          Configparser
    """
    cp = TypedConfigParser()

    if 'extra_parsers' in kwargs:
        for extra_parser in kwargs.pop('extra_parsers'):
            cp.add_parser(*extra_parser)

    cp.readfp(fileobj)
    cp.read(filenames)
    cp.parse_all()

    args = kwargs.pop('args', None)

    op = OptionParser(**kwargs)
        
    for section in cp.sections():
        if section == '__main__':
            og = op
            tpl = '--%(option)s'
        else:
            og = op.add_option_group(section)
            tpl = '--%(section)s-%(option)s'
        for optname in cp.options(section):
            option = cp.get(section, optname)
            if 'help' in option.attrs:
                option.attrs['help'] %= option.attrs
            if option.is_empty:
                default = None
            else:
                default = option.value
            og.add_option(tpl % {'section': section.lower(),
                                 'option': optname.lower()},
                          **dict(option.attrs, default=default))
                
    options, args = op.parse_args(args)

    for section in cp.sections():
        for optname, optval in cp.items(section):
            optname = normoptname(cp, section, optname)
            value = getattr(options, optname)
            if optval.value != value:
                # the value has been overridden by an argument;
                # re-parse it.
                setattr(options, optname, optval.parser(value))

    return op, options, args

from configglue.pyschema import schemaconfigglue, ini2schema
def configglue(fileobj, args=None):
    return schemaconfigglue(ini2schema(fileobj),
                            argv=args)
