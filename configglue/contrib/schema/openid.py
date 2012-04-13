from configglue.schema import (
    BoolOption,
    DictOption,
    IntOption,
    ListOption,
    Schema,
    Section,
    StringOption,
    TupleOption,
    )


class OpenIdSchema(Schema):
    class openid(Section):
        pre_authorization_validity = IntOption()
        openid_preauthorization_acl = ListOption(
            item=TupleOption(length=2))
        openid_create_users = BoolOption()
        openid_launchpad_teams_mapping = DictOption()
        openid_sso_server_url = StringOption()
        openid_set_language_from_sreg = BoolOption()
        openid_sreg_extra_fields = ListOption(item=StringOption())
        openid_launchpad_staff_teams = ListOption(item=StringOption())
