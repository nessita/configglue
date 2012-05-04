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
from .django_openid_auth import DjangoOpenIdAuthSchema
from .preflight import PreflightSchema
from .saml2idp import Saml2IdpSchema
from .raven import RavenSchema
from .pystatsd import PyStatsdSchema


__all__ = [
    'DevServerSchema',
    'DjangoJenkinsSchema',
    'NexusSchema',
    'DjangoOpenIdAuthSchema',
    'PreflightSchema',
    'Saml2IdpSchema',
    'RavenSchema',
    'PyStatsdSchema',
    ]
