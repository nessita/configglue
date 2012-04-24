from configglue.schema import Section, Schema, StringOption


class PreflightSchema(Schema):
    """Configglue schema for django-preflight."""

    __version__ = '0.1'

    class preflight(Section):
        preflight_base_template = StringOption(
            default='index.1col.html')
        preflight_table_class = StringOption(
            default='listing')
