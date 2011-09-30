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

import json
from ConfigParser import (
    NoSectionError,
    NoOptionError,
)
from copy import deepcopy
from inspect import getmembers


__all__ = [
    'BoolOption',
    'Option',
    'Section',
    'DictOption',
    'IntOption',
    'ListOption',
    'Schema',
    'StringOption',
    'TupleOption',
    'merge',
]

NO_DEFAULT = object()


def get_config_objects(obj):
    """Return the list of Section- and Option-derived objects."""
    objects = []
    for name, obj in getmembers(obj):
        if isinstance(obj, (Section, Option)):
            objects.append((name, obj))
        elif type(obj) == type and issubclass(obj, Section):
            instance = obj()
            for key, value in get_config_objects(obj):
                setattr(instance, key, value)
            objects.append((name, instance))
    return objects


def merge(*schemas):
    # import here to avoid circular imports
    from .parser import SchemaValidationError

    # define result schema
    class MergedSchema(Schema):
        pass

    # for each schema
    for schema in schemas:
        instance = schema()
        # iterate over the schema sections
        for section in instance.sections():
            # create the appropriate section object
            section_name = section.name
            if section_name == '__main__':
                # section is special __main__ section
                sect = MergedSchema
            elif not hasattr(MergedSchema, section_name):
                # section is not present in schema, just copy it over
                # completely
                setattr(MergedSchema, section_name, section)
                continue
            else:
                # section is present in schema, do the merge
                sect = getattr(MergedSchema, section_name)

            # do the merge

            # iterate over the section options
            for option in section.options():
                opt = getattr(sect, option.name, None)
                if opt is not None:
                    if option != opt:
                        raise SchemaValidationError("Conflicting option "
                            "'%s.%s' while merging schemas." % (
                            section_name, option.name))
                else:
                    setattr(sect, option.name, option)

    return MergedSchema


class Schema(object):
    """A complete description of a system configuration.

    To define your own configuration schema you should:
     1- Inherit from Schema
     2- Add Options and Sections as class attributes.

    With that your whole configuration schema is defined, and you can now
    load configuration files.

    Options that don't go in a Section will belong in the
    '__main__' section of the configuration files.

    One Option comes already defined in Schema, 'includes' in the
    '__main__' section, that allows configuration files to include other
    configuration files.

    """

    def __init__(self):
        self.includes = ListOption(item=StringOption())
        self._sections = {}
        # add section and options to the schema
        for name, item in get_config_objects(self.__class__):
            self._add_item(name, item)

    def _add_item(self, name, item):
        """Add a top-level item to the schema."""
        item.name = name
        if isinstance(item, Section):
            self._add_section(name, item)
        elif isinstance(item, Option):
            self._add_option(name, item)
        # override class attributes with instance attributes to correctly
        # handle schema inheritance
        setattr(self, name, deepcopy(item))

    def _add_section(self, name, section):
        """Add a top-level section to the schema."""
        self._sections[name] = section
        for opt_name, opt in get_config_objects(section):
            opt.name = opt_name
            opt.section = section

    def _add_option(self, name, option):
        """Add a top-level option to the schema."""
        section = self._sections.setdefault('__main__',
            Section(name='__main__'))
        option.section = section
        setattr(section, name, option)

    def __eq__(self, other):
        return (
            type(self) == type(other) and
            self._sections == other._sections and
            self.includes == other.includes)

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_valid(self):
        """Return whether the schema has a valid structure."""
        explicit_default_section = isinstance(getattr(self, '__main__', None),
                                              Section)
        is_valid = not explicit_default_section
        return is_valid

    def has_section(self, name):
        """Return True if a Section with the given name is available"""
        return name in self._sections.keys()

    def section(self, name):
        """Return a Section by name"""
        section = self._sections.get(name)
        if section is None:
            raise NoSectionError(name)
        return section

    def sections(self):
        """Returns the list of available Sections"""
        return self._sections.values()

    def options(self, section=None):
        """Return all the Options within a given section.

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
            class_config_objects = get_config_objects(self.__class__)
            options = [getattr(self, att) for att, _ in class_config_objects
                           if isinstance(getattr(self, att), Option)]
        else:
            options = section.options()
        return options


class Section(object):
    """A group of options.

    This class is just a bag you can dump Options in.

    After instantiating the Schema, each Section will know its own
    name.

    """
    def __init__(self, name=''):
        self.name = name

    def __eq__(self, other):
        return (
            type(self) == type(other) and
            self.name == other.name and
            self.options() == other.options())

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        if self.name:
            name = " %s" % self.name
        else:
            name = ''
        value = "<{0}{1}>".format(self.__class__.__name__, name)
        return value

    def has_option(self, name):
        """Return True if a Option with the given name is available"""
        opt = getattr(self, name, None)
        return isinstance(opt, Option)

    def option(self, name):
        """Return a Option by name"""
        opt = getattr(self, name, None)
        if opt is None:
            raise NoOptionError(name, self.name)
        return opt

    def options(self):
        """Return a list of all available Options within this section"""
        return [getattr(self, att) for att in vars(self)
                if isinstance(getattr(self, att), Option)]


class Option(object):
    """Base class for Config Options.

    Options are never bound to a particular conguration file, and
    simply describe one particular available option.

    They also know how to parse() the content of a config file in to the right
    type of object.

    If self.raw == True, then variable interpolation will not be carried out
    for this config option.

    If self.require_parser == True, then the parse() method will have a second
    argument, parser, that should receive the whole SchemaConfigParser to
    do the parsing.  This is needed for config options that need to look at
    other parts of the config file to be able to carry out their parsing,
    like DictOption.

    If self.fatal == True, SchemaConfigParser's parse_all will raise an
    exception if no value for this option is provided in the configuration
    file.  Otherwise, the self.default value will be used if the option is
    omitted.

    In runtime, after instantiating the Schema, each Option will also
    know its own name and to which section it belongs.

    """

    require_parser = False

    def __init__(self, name='', raw=False, default=NO_DEFAULT, fatal=False,
                 help='', section=None, action='store', short_name=''):
        self.name = name
        self.short_name = short_name
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
            equal = (
                type(self) == type(other) and
                self.name == other.name and
                self.short_name == other.short_name and
                self.raw == other.raw and
                self.fatal == other.fatal and
                self.default == other.default and
                self.help == other.help and
                self.action == other.action)
            if self.section is not None and other.section is not None:
                # sections might be different while the options are the
                # same; the section names though should be the same
                equal &= self.section.name == other.section.name
            else:
                equal &= (self.section is None and other.section is None)
        except AttributeError:
            equal = False

        return equal

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        extra = ' raw' if self.raw else ''
        extra += ' fatal' if self.fatal else ''
        section = self.section.name if self.section is not None else None
        if section is not None:
            name = " {0}.{1}".format(section, self.name)
        elif self.name:
            name = " {0}".format(self.name)
        else:
            name = ''
        value = "<{0}{1}{2}>".format(self.__class__.__name__, name, extra)
        return value

    def _get_default(self):
        return None

    def parse(self, value, raw=False):
        """Parse the given value."""
        raise NotImplementedError()

    def validate(self, value):
        raise NotImplementedError()

    def to_string(self, value):
        """Return a string representation of the value."""
        return str(value)


class BoolOption(Option):
    """A Option that is parsed into a bool"""

    def _get_default(self):
        return False

    def parse(self, value, raw=False):
        """Parse the given value.

        If *raw* is *True*, return the value unparsed.

        """
        if raw:
            return value

        if value.lower() in ['y', '1', 'yes', 'on', 'true']:
            return True
        elif value.lower() in ['n', '0', 'no', 'off', 'false']:
            return False
        else:
            raise ValueError("Unable to determine boolosity of %r" % value)

    def validate(self, value):
        return isinstance(value, bool)


class IntOption(Option):
    """A Option that is parsed into an int"""

    def _get_default(self):
        return 0

    def parse(self, value, raw=False):
        """Parse the given value.

        If *raw* is *True*, return the value unparsed.

        """
        if raw:
            return value

        return int(value)

    def validate(self, value):
        return isinstance(value, int)


class ListOption(Option):
    """A Option that is parsed into a list of objects

    All items in the list need to be of the same type.  The 'item' constructor
    argument determines the type of the list items. item should be another
    child of Option.

    self.require_parser will be True if the item provided in turn has
    require_parser == True.

    if remove_duplicates == True, duplicate elements in the lines will be
    removed.  Only the first occurrence of any item will be kept,
    otherwise the general order of the list will be preserved.

    """

    def __init__(self, name='', item=None, raw=False, default=NO_DEFAULT,
        fatal=False, help='', action='store', remove_duplicates=False,
        short_name='', parse_json=True):
        super(ListOption, self).__init__(name=name, raw=raw,
            default=default, fatal=fatal, help=help, action=action,
            short_name=short_name)
        if item is None:
            item = StringOption()
        self.item = item
        self.require_parser = item.require_parser
        self.raw = raw or item.raw
        self.remove_duplicates = remove_duplicates
        self.parse_json = parse_json

    def __eq__(self, other):
        equal = super(ListOption, self).__eq__(other)
        if equal:
            # we can be sure both objects are of the same type by now
            equal &= (self.item == other.item and
                self.require_parser == other.require_parser and
                self.raw == other.raw and
                self.remove_duplicates == other.remove_duplicates)

        return equal

    def _get_default(self):
        return []

    def parse(self, value, parser=None, raw=False):
        """Parse the given value.

        A *parser* object is used to parse individual list items.
        If *raw* is *True*, return the value unparsed.

        """
        def _parse_item(value):
            if self.require_parser:
                value = self.item.parse(value, parser=parser, raw=raw)
            else:
                value = self.item.parse(value, raw=raw)
            return value

        is_json = self.parse_json
        if is_json:
            try:
                parsed = json.loads(value)
                is_json = isinstance(parsed, list)
            except:
                is_json = False

        if not is_json:
            parsed = [_parse_item(x) for x in value.split('\n') if len(x)]

        if self.remove_duplicates:
            filtered_items = []
            for item in parsed:
                if not item in filtered_items:
                    filtered_items.append(item)
            parsed = filtered_items
        return parsed

    def validate(self, value):
        return isinstance(value, list)

    def to_string(self, value):
        if self.parse_json:
            return json.dumps(value)
        else:
            return super(ListOption, self).to_string(value)


class StringOption(Option):
    """A Option that is parsed into a string.

    If null==True, a value of 'None' will be parsed in to None instead of
    just leaving it as the string 'None'.

    """

    def __init__(self, name='', raw=False, default=NO_DEFAULT, fatal=False,
        null=False, help='', action='store', short_name=''):
        self.null = null
        super(StringOption, self).__init__(name=name, raw=raw,
            default=default, fatal=fatal, help=help, action=action,
            short_name=short_name)

    def __eq__(self, other):
        equal = super(StringOption, self).__eq__(other)
        if equal:
            # we can be sure both objects are of the same type by now
            equal &= self.null == other.null

        return equal

    def _get_default(self):
        return '' if not self.null else None

    def parse(self, value, raw=False):
        """Parse the given value.

        If *raw* is *True*, return the value unparsed.

        """
        if raw:
            result = value
        elif self.null:
            result = None if value in (None, 'None') else value
        elif isinstance(value, basestring):
            result = value
        else:
            result = repr(value)
        return result

    def to_string(self, value):
        if value is None and self.null:
            return 'None'
        return value

    def validate(self, value):
        return (self.null and value is None) or isinstance(value, basestring)


class TupleOption(Option):
    """A Option that is parsed into a fixed-size tuple of strings.

    The number of items in the tuple should be specified with the 'length'
    constructor argument.

    """

    def __init__(self, name='', length=0, raw=False, default=NO_DEFAULT,
        fatal=False, help='', action='store', short_name=''):
        super(TupleOption, self).__init__(name=name, raw=raw,
            default=default, fatal=fatal, help=help, action=action,
            short_name=short_name)
        self.length = length

    def __eq__(self, other):
        equal = super(TupleOption, self).__eq__(other)
        if equal:
            # we can be sure both objects are of the same type by now
            equal &= self.length == other.length

        return equal

    def _get_default(self):
        return ()

    def parse(self, value, raw=False):
        """Parse the given value.

        If *raw* is *True*, return the value unparsed.

        """
        parts = [part.strip() for part in value.split(',')]
        if parts == ['()']:
            result = ()
        elif self.length:
            # length is not 0, so length validation
            if len(parts) == self.length:
                result = tuple(parts)
            else:
                raise ValueError(
                    "Tuples need to be %d items long" % self.length)
        else:
            result = tuple(parts)
            # length is 0, so no length validation
        return result

    def validate(self, value):
        return isinstance(value, tuple)


class DictOption(Option):
    """A Option that is parsed into a dictionary.

    In the configuration file you'll need to specify the name of a section,
    and all that section's items will be parsed as a dictionary.

    The available keys for the dict are specified with the 'spec' constructor
    argument, that should be in turn a dictionary.  spec's keys are the
    available keys for the config file, and spec's values should be
    Options that will be used to parse the values in the config file.

    """

    require_parser = True

    def __init__(self, name='', spec=None, strict=False, raw=False,
                 default=NO_DEFAULT, fatal=False, help='', action='store',
                 item=None, short_name='', parse_json=True):
        if spec is None:
            spec = {}
        if item is None:
            item = StringOption()
        self.spec = spec
        self.strict = strict
        self.item = item
        self.parse_json = parse_json
        super(DictOption, self).__init__(name=name, raw=raw,
            default=default, fatal=fatal, help=help, action=action,
            short_name=short_name)

    def __eq__(self, other):
        equal = super(DictOption, self).__eq__(other)
        if equal:
            # we can be sure both objects are of the same type by now
            equal &= (self.spec == other.spec and
                self.strict == other.strict and
                self.item == other.item)

        return equal

    def _get_default(self):
        default = {}
        for key, value in self.spec.items():
            default[key] = value.default
        return default

    def parse(self, value, parser, raw=False):
        """Parse the given value.

        A *parser* object is used to parse individual dict items.
        If *raw* is *True*, return the value unparsed.

        """
        is_json = self.parse_json
        if is_json:
            try:
                parsed = json.loads(value)
                is_json = isinstance(parsed, dict)
            except:
                is_json = False

        if not is_json:
            # process extra sections
            sections = value.split()
            parser.extra_sections.update(set(sections))
            for name in sections:
                nested = self.get_extra_sections(name, parser)
                parser.extra_sections.update(set(nested))

            parsed = dict(parser.items(value))

        result = {}
        # parse config items according to spec
        for key, value in parsed.items():
            if self.strict and not key in self.spec:
                raise ValueError("Invalid key %s in section %s" % (
                    key, value))
            option = self.spec.get(key, None)
            if option is None:
                # option not part of spec, but we are in non-strict mode
                # parse it using the default item parser
                option = self.item

            if not option.validate(value):
                # parse option
                kwargs = {}
                if option.require_parser:
                    kwargs['parser'] = parser
                if not raw:
                    value = option.parse(value, **kwargs)
            result[key] = value

        # fill in missing items with default values
        for key in self.spec:
            if not key in parsed:
                option = self.spec[key]
                if option.fatal:
                    raise ValueError("No option '%s' in section '%s'" %
                        (key, value))
                else:
                    if not raw:
                        value = option.default
                    else:
                        value = unicode(option.default)
                    result[key] = value
        return result

    def validate(self, value):
        return isinstance(value, dict)

    def to_string(self, value):
        if self.parse_json:
            return json.dumps(value)
        else:
            return super(DictOption, self).to_string(value)

    def get_extra_sections(self, section, parser):
        """Return the list of implicit sections.

        Implicit sections are sections defined in the configuration file
        that are not defined in the schema, but used as helper sections for
        defining a dictionary.

        """
        sections = []
        for option in parser.options(section):
            option_obj = self.spec.get(option, self.item)
            is_dict_item = isinstance(option_obj, DictOption)
            is_dict_lines_item = (hasattr(option_obj, 'item') and
                isinstance(option_obj.item, DictOption))

            if not (is_dict_item or is_dict_lines_item):
                continue

            if is_dict_item:
                base = option_obj
            else:
                base = option_obj.item

            value = parser.get(section, option, parse=False)
            names = value.split()
            sections.extend(names)

            # recurse
            for name in names:
                extra = base.get_extra_sections(name, parser)
                sections.extend(extra)

        return sections
