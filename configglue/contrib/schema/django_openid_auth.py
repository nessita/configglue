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
from configglue.schema import (
    BoolOption,
    DictOption,
    ListOption,
    Schema,
    Section,
    StringOption,
    )


class DjangoOpenIdAuthSchema(Schema):
    """Configglue schema for django-openid-auth."""

    __version__ = '0.5'

    class openid(Section):
        openid_use_as_admin_login = BoolOption(
            default=False)
        openid_create_users = BoolOption(
            default=False)
        openid_update_details_from_sreg = BoolOption(
            default=False)
        openid_physical_multifactor_required = BoolOption(
            default=False)
        openid_strict_usernames = BoolOption(
            default=False)
        openid_sreg_required_fields = ListOption(
            item=StringOption())
        openid_sreg_extra_fields = ListOption(
            item=StringOption())
        openid_follow_renames = BoolOption(
            default=False)
        openid_launchpad_teams_mapping_auto = BoolOption(
            default=False)
        openid_launchpad_teams_mapping_auto_blacklist = ListOption(
            item=StringOption())
        openid_launchpad_teams_mapping = DictOption()
        openid_launchpad_staff_teams = ListOption(
            item=StringOption())
        openid_launchpad_teams_required = ListOption(
            item=StringOption())
        openid_disallow_inames = BoolOption(
            default=False)
        allowed_external_openid_redirect_domains = ListOption(
            item=StringOption())
        openid_trust_root = StringOption()
        openid_sso_server_url = StringOption(
            null=True)
        openid_email_whitelist_regexp_list = ListOption(
            item=StringOption())
