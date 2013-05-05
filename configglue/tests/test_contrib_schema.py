from unittest import TestCase

from configglue.schema import ListOption, StringOption
from configglue.contrib.schema import DjangoOpenIdAuthSchema


class DjangoOpenIdAuthSchemaTestCase(TestCase):

    def test_openid_launchpad_teams_required_option(self):
        schema = DjangoOpenIdAuthSchema()
        option = schema.openid.openid_launchpad_teams_required
        self.assertTrue(isinstance(option, ListOption))
        self.assertTrue(isinstance(option.item, StringOption))
