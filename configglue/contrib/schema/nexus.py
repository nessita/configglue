from configglue.schema import BoolOption, Schema, Section, StringOption


class NexusSchema(Schema):
    class nexus(Section):
        nexus_media_prefix = StringOption(default='/nexus/media/')
        nexus_use_django_media_url = BoolOption()
