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
from configglue.schema import IntOption, Schema, Section, StringOption


class PyStatsdSchema(Schema):
    """Configglue schema for pystatsd."""

    __version__ = '0.1.6'

    class statsd(Section):
        statsd_host = StringOption(
            default='localhost')
        statsd_port = IntOption(
            default=8125)
