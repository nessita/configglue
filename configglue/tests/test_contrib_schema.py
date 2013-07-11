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
from unittest import TestCase

from configglue.schema import ListOption, StringOption
from configglue.contrib.schema import DjangoOpenIdAuthSchema


class DjangoOpenIdAuthSchemaTestCase(TestCase):

    def test_openid_launchpad_teams_required_option(self):
        schema = DjangoOpenIdAuthSchema()
        option = schema.openid.openid_launchpad_teams_required
        self.assertTrue(isinstance(option, ListOption))
        self.assertTrue(isinstance(option.item, StringOption))

    def test_openid_email_whitelist_regexp_list_option(self):
        schema = DjangoOpenIdAuthSchema()
        option = schema.openid.openid_email_whitelist_regexp_list
        self.assertTrue(isinstance(option, ListOption))
        self.assertTrue(isinstance(option.item, StringOption))
