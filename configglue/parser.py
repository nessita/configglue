###############################################################################
#
# configglue -- glue for your apps' configuration
#
# A library for simple, DRY configuration of applications
#
# (C) 2009--2013 by Canonical Ltd.
# by John R. Lenton <john.lenton@canonical.com>
# and Ricardo Kirkner <ricardo.kirkner@canonical.com>
#
# Released under the BSD License (see the file LICENSE)
#
# For bug reports, support, and new releases: http://launchpad.net/configglue
#
###############################################################################

import codecs
import collections
import copy
import logging
import os
import re

from functools import reduce

from ._compat import BaseConfigParser, text_type, string_types
from ._compat import (
    DEFAULTSECT,
    InterpolationMissingOptionError,
    NoOptionError,
    NoSectionError,
)


__all__ = [
    'SchemaValidationError',
    'SchemaConfigParser',
]

CONFIG_FILE_ENCODING = 'utf-8'

class NullHandler(logging.Handler):
    def emit(self, record):
        pass


logger = logging.getLogger(__name__)
logger.addHandler(NullHandler())


class SchemaValidationError(Exception):
    """Exception class raised for any schema validation error."""


class SchemaConfigParser(BaseConfigParser, object):
    """A ConfigParser that validates against a Schema

    The way to use this class is:

    config = SchemaConfigParser(MySchema())
    config.read('mysystemconfig.cfg', 'mylocalconfig.cfg', ...)
    config.parse_all()
    ...
    profit!

    """
    def __init__(self, schema):
        super(SchemaConfigParser, self).__init__()
        # validate schema
        if not schema.is_valid():
            # TODO: add error details
            raise SchemaValidationError()
        self.schema = schema
        self._location = {}
        self.extra_sections = set()
        self._basedir = ''
        self._dirty = collections.defaultdict(
            lambda: collections.defaultdict(dict))

    def is_valid(self, report=False):
        """Return if the state of the parser is valid.

        This is useful to detect errors in configuration files, like type
        errors or missing required options.

        """
        valid = True
        errors = []
        try:
            # validate structure
            config_sections = set(self.sections())
            schema_sections = set(s.name for s in self.schema.sections())
            skip_sections = self.extra_sections
            magic_sections = set(['__main__', '__noschema__'])
            # test1: no undefined implicit sections
            unmatched_sections = (skip_sections - config_sections)
            if unmatched_sections:
                error_msg = "Undefined sections in configuration: %s"
                error_value = ', '.join(unmatched_sections)
                errors.append(error_msg % error_value)
                valid = False
            # remove sections to skip from config sections
            config_sections.difference_update(skip_sections)
            # test2: no extra sections that are not implicit sections
            unmatched_sections = (
                config_sections - magic_sections - schema_sections)
            if unmatched_sections:
                error_msg = "Sections in configuration are missing from schema: %s"
                error_value = ', '.join(unmatched_sections)
                errors.append(error_msg % error_value)
                valid = False

            for name in config_sections.union(schema_sections):
                if name not in skip_sections:
                    if not self.schema.has_section(name):
                        # this should have been reported before
                        # so skip bogus section
                        continue

                    section = self.schema.section(name)
                    try:
                        parsed_options = set(self.options(name))
                    except NoSectionError:
                        parsed_options = set([])
                    schema_options = set(section.options())

                    fatal_options = set(opt.name for opt in schema_options
                                        if opt.fatal)
                    # all fatal options are included
                    fatal_included = parsed_options.issuperset(fatal_options)
                    if not fatal_included:
                        error_msg = ("Configuration missing required options"
                                     " for section '%s': %s")
                        error_value = ', '.join(list(fatal_options -
                                                     parsed_options))
                        errors.append(error_msg % (name, error_value))
                    valid &= fatal_included

                    # remaining parsed options are valid schema options
                    other_options = parsed_options - fatal_options
                    schema_opt_names = set(opt.name for opt in schema_options)

                    # add the default section special includes option
                    if name == '__main__':
                        schema_opt_names.add('includes')

                    schema_options = other_options.issubset(schema_opt_names)
                    if not schema_options:
                        error_msg = ("Configuration includes invalid options"
                                     " for section '%s': %s")
                        error_value = ', '.join(list(other_options -
                                                     schema_opt_names))
                        errors.append(error_msg % (name, error_value))
                    valid &= schema_options

            # structure validates, validate content
            self.parse_all()

        except Exception as e:
            errors.append(text_type(e))
            valid = False

        if report:
            return valid, errors
        else:
            return valid

    def items(self, section, raw=False, vars=None):
        """Return the list of all options in a section.

        The returned value is a list of tuples of (name, value) for each
        option in the section.

        All % interpolations are expanded in the return values, based on the
        defaults passed into the constructor, unless the optional argument
        `raw' is true.  Additional substitutions may be provided using the
        `vars' argument, which must be a dictionary whose contents overrides
        any pre-existing defaults.

        The section __main__ is special as it's implicitly defined and used
        for options not explicitly included in any section.

        """
        d = self._defaults.copy()
        try:
            d.update(self._sections[section])
        except KeyError:
            if section != DEFAULTSECT:
                raise NoSectionError(section)
        # Update with the entry specific variables
        if vars:
            for key, value in vars.items():
                d[self.optionxform(key)] = value
        options = d.keys()
        if "__name__" in options:
            options.remove("__name__")
        if raw:
            return [(option, d[option])
                    for option in options]
        else:
            items = []
            for option in options:
                try:
                    value = self._interpolate(section, option, d[option], d)
                except InterpolationMissingOptionError as e:
                    # interpolation failed, because key was not found in
                    # section. try other sections before bailing out
                    value = self._interpolate_value(section, option)
                    if value is None:
                        # this should be a string, so None indicates an error
                        raise e
                items.append((option, value))
            return items

    def values(self, section=None, parse=True):
        """Returns multiple values in a dict.

        This method can return the value of multiple options in a single call,
        unlike get() that returns a single option's value.

        If section=None, return all options from all sections.
        If section is specified, return all options from that section only.

        Section is to be specified *by name*, not by
        passing in real Section objects.

        """
        values = collections.defaultdict(dict)
        if section is None:
            sections = self.schema.sections()
        else:
            sections = [self.schema.section(section)]

        for sect in sections:
            for opt in sect.options():
                values[sect.name][opt.name] = self.get(
                    sect.name, opt.name, parse=parse)
        if section is not None:
            return values[section]
        else:
            return values

    def read(self, filenames, already_read=None):
        """Like ConfigParser.read, but consider files we've already read."""
        if already_read is None:
            already_read = set()
        if isinstance(filenames, string_types):
            filenames = [filenames]
        read_ok = []
        for filename in filenames:
            path = os.path.join(self._basedir, filename)
            if path in already_read:
                continue
            try:
                fp = codecs.open(path, 'r', encoding=CONFIG_FILE_ENCODING)
            except IOError:
                logger.warn(
                    'File {0} could not be read. Skipping.'.format(path))
                continue
            # parse file
            sub_parser = self.__class__(self.schema)
            sub_parser._basedir = self._basedir
            sub_parser._location = self._location
            sub_parser._read(fp, path, already_read=already_read)
            # update current parser with those values
            for section, options in sub_parser._sections.items():
                if section == '__main__':
                    # skip copying includes to avoid including same files twice
                    options.pop('includes', None)
                if section in self._sections:
                    self._sections[section].update(options)
                else:
                    self._sections[section] = options

            fp.close()
            read_ok.append(path)
            self._last_location = filename
        return read_ok

    def readfp(self, fp, filename=None):
        """Like ConfigParser.readfp, but consider the encoding."""
        # wrap the StringIO so it can read encoded text
        decoded_fp = codecs.getreader(CONFIG_FILE_ENCODING)(fp)
        self._read(decoded_fp, filename)

    def _read(self, fp, fpname, already_read=None):
        # read file content
        self._update(fp, fpname)

        if already_read is None:
            already_read = set()
        already_read.add(fpname)

        if self.has_option('__main__', 'includes'):
            old_basedir, self._basedir = self._basedir, os.path.dirname(
                fpname)
            includes = self.get('__main__', 'includes')
            filenames = [text_type.strip(x) for x in includes]

            # parse included files
            sub_parser = self.__class__(self.schema)
            sub_parser._basedir = self._basedir
            sub_parser._location = self._location
            sub_parser.read(filenames)
            # update current parser with those values
            for section, options in sub_parser._sections.items():
                if section == '__main__':
                    # skip copying includes to avoid including same files twice
                    options.pop('includes', None)
                if section in self._sections:
                    self._sections[section].update(options)
                else:
                    self._sections[section] = options

            self._basedir = old_basedir

            if filenames:
                # re-read the file to override included options with
                # local values
                fp.seek(0)
                self._update(fp, fpname)

    def _update(self, fp, fpname):
        # remember current values
        old_sections = copy.deepcopy(self._sections)
        # read in new file
        super(SchemaConfigParser, self)._read(fp, fpname)
        # update location of changed values
        self._update_location(old_sections, fpname)

    def _update_location(self, old_sections, filename):
        # keep list of valid options to include locations for
        option_names = [x.name for x in self.schema.options()]

        # new values
        sections = self._sections

        # update locations
        for section, options in sections.items():
            old_section = old_sections.get(section)
            if old_section is not None:
                # update options in existing section
                for option, value in options.items():
                    valid_option = option in option_names
                    option_changed = (option not in old_section or
                                      value != old_section[option])
                    if valid_option and option_changed:
                        self._location[option] = filename
            else:
                # complete section is new
                for option, value in options.items():
                    valid_option = option in option_names
                    if valid_option:
                        self._location[option] = filename

    def parse(self, section, option, value):
        """Parse the value of an option.

        This method raises NoSectionError if an invalid section name is
        passed in.

        This method raises ValueError if the value is not parseable.

        """
        if section == '__main__':
            option_obj = getattr(self.schema, option, None)
        else:
            section_obj = getattr(self.schema, section, None)
            if section_obj is not None:
                option_obj = getattr(section_obj, option, None)
            else:
                raise NoSectionError(section)

        if option_obj is not None:
            kwargs = {}
            if option_obj.require_parser:
                kwargs = {'parser': self}

            try:
                value = option_obj.parse(value, **kwargs)
            except ValueError as e:
                raise ValueError("Invalid value '%s' for %s '%s' in"
                    " section '%s'. Original exception was: %s" %
                    (value, option_obj.__class__.__name__, option,
                     section, e))
        return value

    def parse_all(self):
        """Go through all sections and options attempting to parse each one.

        If any options are omitted from the config file, provide the
        default value from the schema.

        In the case of an NoSectionError or NoOptionError, raise it if the
        option has *fatal* set to *True*.

        """
        for section in self.schema.sections():
            for option in section.options():
                try:
                    self.get(section.name, option.name, raw=option.raw)
                except (NoSectionError, NoOptionError):
                    if option.fatal:
                        raise

    def locate(self, option=None):
        """Return the location (file) where the option was last defined."""
        return self._location.get(option)

    def _extract_interpolation_keys(self, item):
        if isinstance(item, (list, tuple)):
            keys = [self._extract_interpolation_keys(x) for x in item]
            keys = reduce(set.union, keys, set())
        else:
            keys = set(self._interpolation._KEYCRE.findall(item))
        # remove invalid key
        if '' in keys:
            keys.remove('')
        return keys

    def _get_interpolation_keys(self, section, option):

        rawval = super(SchemaConfigParser, self).get(section, option, raw=True)
        try:
            opt = self.schema.section(section).option(option)
            value = opt.parse(rawval, raw=True)
        except:
            value = rawval

        keys = self._extract_interpolation_keys(value)
        return rawval, keys

    def _interpolate(self, *args, **kwargs):
        """Helper method for transition to configparser."""
        return self._interpolation.before_get(self, *args, **kwargs)

    def _interpolate_value(self, section, option):
        rawval, keys = self._get_interpolation_keys(section, option)
        if not keys:
            # interpolation keys are not valid
            return

        values = {}
        # iterate over the other sections
        for key in keys:
            # we want the unparsed value
            try:
                value = self.get(section, key, parse=False)
            except (NoSectionError, NoOptionError):
                # value of key not found in config, so try in special
                # sections
                for section in ('__main__', '__noschema__'):
                    try:
                        value = super(SchemaConfigParser, self).get(section,
                                                                    key)
                        break
                    except:
                        continue
                else:
                    return
            values[key] = value

        # replace holders with values
        result = rawval % values

        assert isinstance(result, string_types)
        return result

    def interpolate_environment(self, rawval, raw=False):
        """Interpolate environment variables"""
        if raw:
            return rawval

        # this allows both nested and mutliple environment variable
        # interpolation in a single value
        pattern = re.sub(r'\${([A-Z_]+)}', r'%(\1)s', rawval)
        pattern = re.sub(r'\$([A-Z_]+)', r'%(\1)s', pattern)

        # counter to protect against infinite loops
        num_interpolations = 0
        # save simple result in case we need it
        simple_pattern = pattern

        # handle complex case of env vars with defaults
        env = os.environ.copy()
        env_re = re.compile(r'\${(?P<name>[A-Z_]+):-(?P<default>.*?)}')
        match = env_re.search(pattern)
        while match and num_interpolations < 50:
            groups = match.groupdict()
            name = groups['name']
            pattern = pattern.replace(match.group(), '%%(%s)s' % name)
            if name not in env and groups['default'] is not None:
                # interpolate defaults as well to allow ${FOO:-$BAR}
                env[name] = groups['default'] % os.environ

            num_interpolations += 1
            match = env_re.search(pattern)

        if num_interpolations >= 50:
            # blown loop, restore earlier simple interpolation
            pattern = simple_pattern

        keys = self._extract_interpolation_keys(pattern)
        if not keys:
            # interpolation keys are not valid
            return rawval

        return pattern % env

    def _get_default(self, section, option):
        # cater for 'special' sections
        if section == '__noschema__':
            value = super(SchemaConfigParser, self).get(section, option)
            return value

        # any other section
        opt = self.schema.section(section).option(option)
        if not opt.fatal:
            value = opt.default
            return value

        # no default value found, raise an error
        raise NoOptionError(option, section)

    def get(self, section, option, raw=False, vars=None, parse=True):
        """Return the parsed value of an option.

        If *raw* is True, return the value as it's stored in the parser,
        without parsing it.

        Extra *vars* can be passed in to be evaluated during parsing.

        If *parse* is False, return the string representation of the value.

        """
        try:
            # get option's raw mode setting
            try:
                option_obj = self._get_option(section, option)
                raw = option_obj.raw or raw
            except:
                pass
            # value is defined entirely in current section
            value = super(SchemaConfigParser, self).get(section, option,
                                                        raw=raw, vars=vars)
        except InterpolationMissingOptionError as e:
            # interpolation key not in same section
            value = self._interpolate_value(section, option)
            if value is None:
                # this should be a string, so None indicates an error
                raise e
        except (NoSectionError, NoOptionError) as e:
            # option not found in config, try to get its default value from
            # schema
            value = self._get_default(section, option)

        # interpolate environment variables
        if isinstance(value, string_types):
            try:
                value = self.interpolate_environment(value, raw=raw)
                if parse:
                    value = self.parse(section, option, value)
            except KeyError:
                # interpolation failed, fallback to default value
                value = self._get_default(section, option)

        return value

    def _get_option(self, section, option):
        section_obj = self.schema.section(section)
        option_obj = section_obj.option(option)
        return option_obj

    def set(self, section, option, value):
        """Set an option's raw value."""
        option_obj = self._get_option(section, option)
        # make sure the value is of the right type for the option
        if not option_obj.validate(value):
            raise TypeError("{0} is not a valid {1} value.".format(
                value, type(option_obj).__name__))
        # cast value to a string because SafeConfigParser only allows
        # strings to be set
        str_value = option_obj.to_string(value)
        if not self.has_section(section):
            # Don't call .add_section here because 2.6 complains
            # about sections called '__main__'
            self._sections[section] = {}
        super(SchemaConfigParser, self).set(section, option, str_value)
        filename = self.locate(option)
        self._dirty[filename][section][option] = str_value

    def write(self, fp):
        """Write an .ini-format representation of the configuration state."""
        # make sure the parser is populated
        self._fill_parser()

        if self._defaults:
            fp.write("[%s]\n" % DEFAULTSECT)
            for (key, value) in self._defaults.items():
                fp.write("%s = %s\n" % (key, value.replace('\n', '\n\t')))
            fp.write("\n")
        for section in self._sections:
            fp.write("[%s]\n" % section)
            for (key, value) in self._sections[section].items():
                if key == "__name__":
                    continue
                if (value is not None) or (self._optcre == self.OPTCRE):
                    key = " = ".join((key, value.replace('\n', '\n\t')))
                fp.write("%s\n" % (key))
            fp.write("\n")

    def save(self, fp=None):
        """Save the parser contents to a file.

        The data will be saved as a ini file.

        """
        if fp is not None:
            if isinstance(fp, string_types):
                fp = codecs.open(fp, 'w', encoding=CONFIG_FILE_ENCODING)
            self.write(fp)
        else:
            # write to the original files
            for filename, sections in self._dirty.items():

                if filename is None:
                    # default option was overridden. figure out where to
                    # save it
                    if not getattr(self, '_last_location', None):
                        # no files where read, there is no possible
                        # location for the customized setting.
                        raise ValueError("No config files where read and no "
                            "location was specified for writing the "
                            "configuration.")
                    else:
                        filename = self._last_location

                parser = BaseConfigParser()
                parser.read(filename)

                for section, options in sections.items():
                    for option, value in options.items():
                        parser.set(section, option, value)

                # write to new file
                parser.write(codecs.open("%s.new" % filename, 'w',
                                         encoding=CONFIG_FILE_ENCODING))
                # rename old file
                if os.path.exists(filename):
                    os.rename(filename, "%s.old" % filename)
                # rename new file
                os.rename("%s.new" % filename, filename)

    def _fill_parser(self):
        """Populate parser with current values for each option."""
        values = self.values()
        for section, options in values.items():
            for option, value in options.items():
                self.set(section, option, value)
        # make sure having set the options didn't change anything
        assert values == self.values()
