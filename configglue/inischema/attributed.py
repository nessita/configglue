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

"""
AttributtedConfigParser lives here.
"""
import re
from ConfigParser import RawConfigParser


marker = object()


class ValueWithAttrs(object):
    """The values returned by AttributtedConfigParser are instances of this.
    """
    def __init__(self, value=marker, **kw):
        self.value = value
        self.attrs = kw

    @property
    def is_empty(self):
        """
        Is the value unset?

        Note this is different from being set to None.
        """
        return self.value is marker


class AttributedConfigParser(RawConfigParser, object):
    """Handle attributed ini-style configuration files
    """
    def optionxform(self, optionstr):
        """See RawConfigParser.optionxform"""
        return optionstr.lower().replace('-', '_')

    def normalized_options(self, section):
        """ Return the section's options, removing the attributes.

        @param section: The section whose filtered options you want
        @return: A C{set} of option names, with attributes removed
        """
        return set(re.sub(r'\..*', '', option)
                   for option in self.options(section))

    def parse_all(self):
        """ Go through all sections and options attempting to parse each one.
        """
        for section in self.sections():
            for option in self.normalized_options(section):
                self.parse(section, option)

    def parse(self, section, option):
        """Parse a single option in a single section.

        @param section: the section within which to look for the option
        @param option: the 'base' option to parse
        """
        if self.has_option(section, option):
            value = ValueWithAttrs(self.get(section, option))
        else:
            value = ValueWithAttrs()
        self.set(section, option, value)
        for opt, val in self.items(section)[:]:
            if opt.startswith(option + '.'):
                value.attrs[opt[len(option) + 1:]] = val
                self.remove_option(section, opt)
