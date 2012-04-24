from configglue.schema import (
    BoolOption,
    IntOption,
    ListOption,
    Schema,
    Section,
    StringOption,
    )


class RavenSchema(Schema):
    """Configglue schema for raven."""

    __version__ = '1.6.1'

    class raven(Section):
        sentry_servers = ListOption()
        sentry_include_paths = ListOption(
            item=StringOption())
        sentry_exclude_paths = ListOption(
            item=StringOption(),
            help='Ignore module prefixes when attempting to discover which '
                'function an error comes from.')
        sentry_timeout = IntOption(
            default=5,
            help='Timeout value for sending messages to remote.')
        sentry_name = StringOption(
            null=True,
            help='This will override the server_name value for this installation.')
        sentry_auto_log_stacks = BoolOption(
            default=False,
            help='Should raven automatically log frame stacks (including '
                'locals) all calls as it would for exceptions.')
        sentry_key = StringOption(
            null=True)
        sentry_max_length_string = IntOption(
            default=200,
            help='The maximum characters of a string that should be stored.')
        sentry_max_length_list = IntOption(
            default=50,
            help='The maximum number of items a list-like container should store.')
        sentry_site = StringOption(
            null=True,
            help='An optional, arbitrary string to identify this client '
                'installation.')
        sentry_public_key = StringOption(
            null=True,
            help='Public key of the project member which will authenticate as '
                'the client.')
        sentry_private_key = StringOption(
            null=True,
            help='Private key of the project member which will authenticate as '
                'the client.')
        sentry_project = IntOption(
            default=1,
            help='Sentry project ID. The default value for installations is 1.')
        sentry_processors = ListOption(
            item=StringOption(),
            default=[
                'raven.processors.SanitizePasswordsProcessor',
                ],
            help='List of processors to apply to events before sending them '
                'to the Sentry server.')
        sentry_dsn = StringOption(
            help='A sentry compatible DSN.')
        sentry_client = StringOption(
            default='raven.contrib.django.DjangoClient')
        sentry_debug = BoolOption(
            default=False)
