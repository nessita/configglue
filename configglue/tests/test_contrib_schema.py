from unittest import TestCase

from configglue.schema import ListOption, StringOption
from configglue.contrib.schema import DjangoOpenIdAuthSchema


class DjangoOpenIdAuthSchemaTestCase(TestCase):

    def test_openid_launchpad_teams_required_option(self):
        schema = DjangoOpenIdAuthSchema()
        option = schema.openid.openid_launchpad_teams_required
        self.assertIsInstance(option, ListOption)
        self.assertIsInstance(option.item, StringOption)

    def test_openid_email_whitelist_regexp_list_option(self):
        schema = DjangoOpenIdAuthSchema()
        option = schema.openid.openid_email_whitelist_regexp_list
        self.assertIsInstance(option, ListOption)
        self.assertIsInstance(option.item, StringOption)
