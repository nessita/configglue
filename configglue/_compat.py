# -*- coding: utf-8 -*-
###############################################################################
#
# configglue -- glue for your apps' configuration
#
# A library for simple, DRY configuration of applications
#
# (C) 2013 by Canonical Ltd.
# by John R. Lenton <john.lenton@canonical.com>
# and Ricardo Kirkner <ricardo.kirkner@canonical.com>
# (C) Python Software Foundation (“PSF”)
#
# Released under the PSF License Agreement (see the file LICENSE.PSF)
#
# For bug reports, support, and new releases: http://launchpad.net/configglue
#
###############################################################################
import re
import sys


PY2 = sys.version_info[0] == 2

if PY2:
    import __builtin__ as builtins
    import ConfigParser as configparser
    from ConfigParser import (
        DEFAULTSECT,
        InterpolationDepthError,
        InterpolationMissingOptionError,
        InterpolationSyntaxError,
        NoOptionError,
        NoSectionError,
        RawConfigParser,
    )

    class BasicInterpolation(object):
        """Interpolation as implemented in the classic ConfigParser.

        The option values can contain format strings which refer to other
        values in the same section, or values in the special default section.

        For example:

            something: %(dir)s/whatever

        would resolve the "%(dir)s" to the value of dir.  All reference
        expansions are done late, on demand. If a user needs to use a
        bare % in a configuration file, she can escape it by writing %%.
        Other % usage is considered a user error and
        raises `InterpolationSyntaxError'."""

        _KEYCRE = re.compile(r"%\(([^)]+)\)s")

        def before_get(self, parser, section, option, value, defaults):
            L = []
            self._interpolate_some(parser, option, L, value, section,
                                defaults, 1)
            return ''.join(L)

        def before_set(self, parser, section, option, value):
            tmp_value = value.replace('%%', '') # escaped percent signs
            tmp_value = self._KEYCRE.sub('', tmp_value) # valid syntax
            if '%' in tmp_value:
                raise ValueError("invalid interpolation syntax in %r at "
                                "position %d" % (value, tmp_value.find('%')))
            return value

        def _interpolate_some(self, parser, option, accum, rest, section, map,
                            depth):
            if depth > configparser.MAX_INTERPOLATION_DEPTH:
                raise configparser.InterpolationDepthError(option, section,
                                                        rest)
            while rest:
                p = rest.find("%")
                if p < 0:
                    accum.append(rest)
                    return
                if p > 0:
                    accum.append(rest[:p])
                    rest = rest[p:]
                # p is no longer used
                c = rest[1:2]
                if c == "%":
                    accum.append("%")
                    rest = rest[2:]
                elif c == "(":
                    m = self._KEYCRE.match(rest)
                    if m is None:
                        raise configparser.InterpolationSyntaxError(option,
                                                                    section,
                            "bad interpolation variable reference %r" % rest)
                    var = parser.optionxform(m.group(1))
                    rest = rest[m.end():]
                    try:
                        v = map[var]
                    except KeyError:
                        raise configparser.InterpolationMissingOptionError(
                            option, section, rest, var)
                    if "%" in v:
                        self._interpolate_some(parser, option, accum, v,
                                            section, map, depth + 1)
                    else:
                        accum.append(v)
                else:
                    raise configparser.InterpolationSyntaxError(
                        option, section,
                        "'%%' must be followed by '%%' or '(', "
                        "found: %r" % (rest,))

    class BaseConfigParser(configparser.SafeConfigParser):
        def __init__(self, *args, **kwargs):
            configparser.SafeConfigParser.__init__(self, *args, **kwargs)

            self._interpolation = BasicInterpolation()

    text_type = unicode
    string_types = (str, unicode)
    iteritems = lambda d: d.iteritems()

else:
    import builtins
    import configparser
    from configparser import (
        DEFAULTSECT,
        InterpolationDepthError,
        InterpolationMissingOptionError,
        InterpolationSyntaxError,
        NoOptionError,
        NoSectionError,
        RawConfigParser,
    )

    BaseConfigParser = configparser.SafeConfigParser
    text_type = str
    string_types = (str,)
    iteritems = lambda d: iter(d.items())
