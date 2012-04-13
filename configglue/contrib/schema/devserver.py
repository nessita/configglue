from configglue.schema import (
    BoolOption,
    IntOption,
    ListOption,
    Section,
    Schema,
    StringOption,
    )


class DevServerSchema(Schema):
    class devserver(Section):
        devserver_ignored_prefixes = ListOption(
            item=StringOption(),
            help="List of url prefixes which will be ignored")
        devserver_modules = ListOption(
            item=StringOption(),
            help="List of devserver modules to enable")
        devserver_default_addr = StringOption(default="127.0.0.1")
        devserver_default_port = StringOption(default="8000")
        devserver_truncate_sql = BoolOption(default=True)
        devserver_ajax_content_length = IntOption(default=300)
        devserver_auto_profile = BoolOption(default=False)

