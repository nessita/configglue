from configglue.schema import (
    BoolOption,
    ListOption,
    Section,
    Schema,
    StringOption,
    )


class Saml2IdpSchema(Schema):
    class saml2(Section):
        saml2idp_autosubmit = BoolOption(default=True)
        saml2idp_issuer = StringOption()
        saml2idp_certificate_file = StringOption()
        saml2idp_private_key_file = StringOption()
        saml2idp_signing = BoolOption(default=True)
        saml2idp_valid_acs = ListOption(
            item=StringOption(),
            help="List of ACS URLs accepted by /+saml login")
        saml2idp_processor_classes = ListOption(
            item=StringOption(),
            help="List of SAML 2.0 AuthnRequest processors")

