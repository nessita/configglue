from configglue.schema import (
    BoolOption,
    ListOption,
    Section,
    Schema,
    StringOption,
    )


class Saml2IdpSchema(Schema):
    """Configglue schema for saml2idp."""

    __version__ = '0.14'

    class saml2(Section):
        saml2idp_autosubmit = BoolOption(
            default=True)
        saml2idp_issuer = StringOption(
            default='http://127.0.0.1:8000')
        saml2idp_certificate_file = StringOption(
            default='keys/certificate.pem')
        saml2idp_private_key_file = StringOption(
            default='keys/private-key.pem')
        saml2idp_signing = BoolOption(
            default=True)
        saml2idp_valid_acs = ListOption(
            item=StringOption(),
            default=[
                'https://login.salesforce.com',
                ],
            help="List of ACS URLs accepted by /+saml login")
        saml2idp_processor_classes = ListOption(
            item=StringOption(),
            default=[
                'saml2idp.salesforce.Processor',
                'saml2idp.google_apps.Processor',
                ],
            help="List of SAML 2.0 AuthnRequest processors")
