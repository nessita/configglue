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
from configglue.schema import BoolOption, Schema, Section, StringOption


class NexusSchema(Schema):
    """Configglue schema for nexus."""

    __version__ = '0.2.3'

    class nexus(Section):
        nexus_media_prefix = StringOption(
            default='/nexus/media/')
        nexus_use_django_media_url = BoolOption(
            default=False)
