from configglue.schema import Section, Schema, StringOption


class PreflightSchema(Schema):
    class preflight(Section):
        preflight_base_template = StringOption()
