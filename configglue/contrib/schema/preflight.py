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
from configglue.schema import Section, Schema, StringOption


class PreflightSchema(Schema):
    """Configglue schema for django-preflight."""

    __version__ = '0.1'

    class preflight(Section):
        preflight_base_template = StringOption(
            default='index.1col.html')
        preflight_table_class = StringOption(
            default='listing')
