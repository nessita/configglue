###############################################################################
#
# configglue -- glue for your apps' configuration
#
# A library for simple, DRY configuration of applications
#
# (C) 2009--2012 by Canonical Ltd.
# by John R. Lenton <john.lenton@canonical.com>
# and Ricardo Kirkner <ricardo.kirkner@canonical.com>
#
# Released under the BSD License (see the file LICENSE)
#
# For bug reports, support, and new releases: http://launchpad.net/configglue
#
###############################################################################

from .devserver import DevServerSchema
from .django_jenkins import DjangoJenkinsSchema
from .nexus import NexusSchema
from .openid import OpenIdSchema
from .preflight import PreflightSchema
from .saml2idp import Saml2IdpSchema
from .sentry import SentrySchema
from .statsd import StatsdSchema


__all__ = [
    'DevServerSchema',
    'DjangoJenkinsSchema',
    'NexusSchema',
    'OpenIdSchema',
    'PreflightSchema',
    'Saml2IdpSchema',
    'SentrySchema',
    'StatsdSchema',
    ]
