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

"""Parsers used by TypedConfigParser live here
"""


def lines(value):
    """ Split a string on its newlines

    RawConfigParser supports "continuations in the style of RFC822", which
    gives us a very natural way of having values that are lists of strings.

    If value isn't a string, leaves it alone.
    """
    try:
        return value.split('\n')
    except AttributeError:
        return value

_true_values = frozenset(('true', '1', 'on', 'yes'))
_false_values = frozenset(('false', '0', 'off', 'no'))


def bool_parser(value):
    """Take a string representation of a boolean and return its boolosity

    true, 1, on, and yes (in any case) should all be True.
    false, 0, off, and no (in any case) should all be False.

    any other string else should raise an error; None and booleans are
    preserved.
    """
    try:
        value = value.lower()
    except AttributeError:
        return bool(value)
    else:
        if value in _true_values:
            return True
        if value in _false_values:
            return False
    raise ValueError("Unable to determine boolosity of %r" % value)
