from configglue.schema import (
    BoolOption,
    IntOption,
    ListOption,
    Section,
    Schema,
    StringOption,
    )


class DevServerSchema(Schema):
    """Configglue schema for django-devserver."""

    __version__ = '0.3.1'

    class devserver(Section):
        devserver_args = ListOption(
            item=StringOption(),
            default=[],
            help='Additional command line arguments to pass to the runserver command (as defaults).')
        devserver_default_addr = StringOption(
            default='127.0.0.1',
            help='The default address to bind to.')
        devserver_default_port = StringOption(
            default='8000',
            help='The default port to bind to.')
        devserver_wsgi_middleware = ListOption(
            item=StringOption(),
            default=[],
            help='A list of additional WSGI middleware to apply to the runserver command.')
        devserver_modules = ListOption(
            item=StringOption(),
            default=[
                'devserver.modules.sql.SQLRealTimeModule',
                ],
            help='List of devserver modules to enable')
        devserver_ignored_prefixes = ListOption(
            item=StringOption(),
            default=['/media', '/uploads'],
            help='List of prefixes to supress and skip process on. By default, '
                'ADMIN_MEDIA_PREFIX, MEDIA_URL and STATIC_URL '
                '(for Django >= 1.3) will be ignored (assuming MEDIA_URL and '
                'STATIC_URL is relative).')
        devserver_truncate_sql = BoolOption(
            default=True,
            help='Truncate SQL queries output by SQLRealTimeModule.')
        devserver_truncate_aggregates = BoolOption(
            default=False)
        devserver_active = BoolOption(
            default=False)
        devserver_ajax_content_length = IntOption(
            default=300,
            help='Maximum response length to dump.')
        devserver_ajax_pretty_print = BoolOption(
            default=False)
        devserver_sql_min_duration = IntOption(
            default=None,
            help='Minimum time a query must execute to be shown, value is in ms.')
        devserver_auto_profile = BoolOption(
            default=False,
            help='Automatically profile all view functions.')
