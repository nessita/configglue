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

from configglue.pyschema import ConfigOption, ConfigSection, super_vars
from configglue.pyschema.options import LinesConfigOption, StringConfigOption


class Schema(object):
    """A complete description of a system configuration.

    To define your own configuration schema you should:
     1- Inherit from Schema
     2- Add ConfigOptions and ConfigSections as class attributes.

    With that your whole configuration schema is defined, and you can now
    load configuration files.

    ConfigOptions that don't go in a ConfigSection will belong in the
    '__main__' section of the configuration files.

    One ConfigOption comes already defined in Schema, 'includes' in the
    '__main__' section, that allows configuration files to include other
    configuration files.
    """
    def __init__(self):
        self.includes = LinesConfigOption(item=StringConfigOption())
        self._sections = {}
        defaultSection = None
        for attname in super_vars(self.__class__):
            att = getattr(self, attname)
            if isinstance(att, ConfigSection):
                att.name = attname
                self._sections[attname] = att
                for optname in super_vars(att):
                    opt = getattr(att, optname)
                    if isinstance(opt, ConfigOption):
                        opt.name = optname
                        opt.section = att
            elif isinstance(att, ConfigOption):
                if defaultSection is None:
                    defaultSection = ConfigSection()
                    defaultSection.name = '__main__'
                    self._sections['__main__'] = defaultSection
                att.name = attname
                att.section = defaultSection
                setattr(defaultSection, attname, att)

    def __eq__(self, other):
        return (self._sections == other._sections and
                self.includes == other.includes)

    def is_valid(self):
        explicit_default_section = isinstance(getattr(self, '__main__', None),
                                              ConfigSection)
        is_valid = not explicit_default_section
        return is_valid

    def has_section(self, name):
        """Return True if a ConfigSection with the given name is available"""
        return name in self._sections.keys()

    def section(self, name):
        """Return a ConfigSection by name"""
        section = self._sections.get(name)
        assert section is not None, "Invalid ConfigSection name '%s'" % name
        return section

    def sections(self):
        """Returns the list of available ConfigSections"""
        return self._sections.values()

    def options(self, section=None):
        """Return all the ConfigOptions within a given section.

        If section is omitted, returns all the options in the configuration
        file, flattening out any sections.
        To get options from the default section, specify section='__main__'
        """
        if isinstance(section, basestring):
            section = self.section(section)
        if section is None:
            options = []
            for s in self.sections():
                options += self.options(s)
        elif section.name == '__main__':
            options = [getattr(self, att) for att in super_vars(self.__class__) 
                           if isinstance(getattr(self, att), ConfigOption)]
        else:
            options = section.options()
        return options


