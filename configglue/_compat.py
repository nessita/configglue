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
import sys


PY2 = sys.version_info[0] == 2

if not PY2:
    import builtins
    import configparser

    text_type = str
    string_types = (str,)
    iteritems = lambda d: iter(d.items())


    class BaseConfigParser(configparser.SafeConfigParser):
        def __init__(self, *args, **kwargs):
            configparser.SafeConfigParser.__init__(self, *args, **kwargs)

            self._KEYCRE = self._interpolation._KEYCRE

else:
    import __builtin__ as builtins
    import ConfigParser as configparser

    from ._compat_parser import BasicInterpolation

    text_type = unicode
    string_types = (str, unicode)
    iteritems = lambda d: d.iteritems()


    class BaseConfigParser(configparser.SafeConfigParser):
        def __init__(self, *args, **kwargs):
            configparser.SafeConfigParser.__init__(self, *args, **kwargs)

            self._interpolation = BasicInterpolation()
