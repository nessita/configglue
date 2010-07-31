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

from configglue.pyschema import ConfigOption, NO_DEFAULT


class BoolConfigOption(ConfigOption):
    """A ConfigOption that is parsed into a bool"""

    def _get_default(self):
        return False

    def parse(self, value, raw=False):
        if raw:
            return value

        if value.lower() in ['y', '1', 'yes', 'on', 'true']:
            return True
        elif value.lower() in ['n', '0', 'no', 'off', 'false']:
            return False
        else:
            raise ValueError("Unable to determine boolosity of %r" % value)


class IntConfigOption(ConfigOption):
    """A ConfigOption that is parsed into an int"""

    def _get_default(self):
        return 0

    def parse(self, value, raw=False):
        if raw:
            return value

        return int(value)


class LinesConfigOption(ConfigOption):
    """A ConfigOption that is parsed into a list of objects

    All items in the list need to be of the same type.  The 'item' constructor
    argument determines the type of the list items. item should be another
    child of ConfigOption.

    self.require_parser will be True if the item provided in turn has
    require_parser == True.

    if remove_duplicates == True, duplicate elements in the lines will be
    removed.  Only the first occurrence of any item will be kept,
    otherwise the general order of the list will be preserved.
    """

    def _get_default(self):
        return []

    def parse(self, value, parser=None, raw=False):
        def _parse_item(value):
            if self.require_parser:
                value = self.item.parse(value, parser=parser, raw=raw)
            else:
                value = self.item.parse(value, raw=raw)
            return value
        items = [_parse_item(x) for x in value.split('\n') if len(x)]
        if self.remove_duplicates:
            filtered_items = []
            for item in items:
                if not item in filtered_items:
                    filtered_items.append(item)
            items = filtered_items
        return items

    def __init__(self, item, raw=False, default=NO_DEFAULT, fatal=False,
        help='', remove_duplicates=False):
        super(LinesConfigOption, self).__init__(raw=raw, default=default,
                                                fatal=fatal, help=help)
        self.item = item
        self.require_parser = item.require_parser
        self.raw = item.raw
        self.remove_duplicates = remove_duplicates

class StringConfigOption(ConfigOption):
    """A ConfigOption that is parsed into a string.

    If null==True, a value of 'None' will be parsed in to None instead of
    just leaving it as the string 'None'.
    """

    def _get_default(self):
        return '' if not self.null else None

    def parse(self, value, raw=False):
        if raw:
            return value

        return unicode(value)

    def __init__(self, raw=False, default=NO_DEFAULT, fatal=False, null=False,
                 help=''):
        self.null = null
        super(StringConfigOption, self).__init__(raw=raw, default=default,
                                                 fatal=fatal, help=help)


class TupleConfigOption(ConfigOption):
    """A ConfigOption that is parsed into a fixed-size tuple of strings.

    The number of items in the tuple should be specified with the 'length'
    constructor argument.
    """

    def __init__(self, length=0, raw=False, default=NO_DEFAULT, fatal=False, help=''):
        super(TupleConfigOption, self).__init__(raw=raw, default=default,
                                                fatal=fatal, help=help)
        self.length = length

    def _get_default(self):
        return ()

    def parse(self, value, raw=False):
        parts = [part.strip() for part in value.split(',')]
        if parts == ['()']:
            result = ()
        elif self.length:
            # length is not 0, so length validation
            if len(parts) == self.length:
                result = tuple(parts)
            else:
                raise ValueError("Tuples need to be %d items long" % self.length)
        else:
            result = tuple(parts)
            # length is 0, so no length validation
        return result


class DictConfigOption(ConfigOption):
    """A ConfigOption that is parsed into a dictionary.

    In the configuration file you'll need to specify the name of a section,
    and all that section's items will be parsed as a dictionary.

    The available keys for the dict are specified with the 'spec' constructor
    argument, that should be in turn a dictionary.  spec's keys are the
    available keys for the config file, and spec's values should be
    ConfigOptions that will be used to parse the values in the config file.
    """
    require_parser = True

    def __init__(self, spec=None, strict=False, raw=False,
                 default=NO_DEFAULT, fatal=False,
                 help='', item=None):
        if spec is None:
            spec = {}
        if item is None:
            item = StringConfigOption()
        self.spec = spec
        self.strict = strict
        self.item = item
        super(DictConfigOption, self).__init__(raw=raw, default=default,
                                               fatal=fatal, help=help)

    def _get_default(self):
        default = {}
        for key, value in self.spec.items():
            default[key] = value.default
        return default

    def parse(self, section, parser=None, raw=False):
        parsed = dict(parser.items(section))
        result = {}

        # parse config items according to spec
        for key, value in parsed.items():
            if self.strict and not key in self.spec:
                raise ValueError("Invalid key %s in section %s" % (key,
                                                                   section))
            option = self.spec.get(key, None)
            if option is None:
                # option not part of spec, but we are in non-strict mode
                # parse it using the default item parser
                option = self.item

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
                        (key, section))
                else:
                    if not raw:
                        value = option.default
                    else:
                        value = unicode(option.default)
                    result[key] = value
        return result

    def get_extra_sections(self, section, parser):
        sections = []
        for option in parser.options(section):
            option_obj = self.spec.get(option, self.item)
            is_dict_item = isinstance(option_obj, DictConfigOption)
            is_dict_lines_item = (hasattr(option_obj, 'item') and
                isinstance(option_obj.item, DictConfigOption))

            if is_dict_item:
                base = option_obj
            elif is_dict_lines_item:
                base = option_obj.item
            else:
                continue

            value = parser.get(section, option, parse=False)
            names = value.split()
            sections.extend(names)

            # recurse
            for name in names:
                extra = base.get_extra_sections(name, parser)
                sections.extend(extra)

        return sections

