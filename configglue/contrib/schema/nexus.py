from configglue.schema import BoolOption, Schema, Section, StringOption


class NexusSchema(Schema):
    """Configglue schema for nexus."""

    __version__ = '0.2.3'

    class nexus(Section):
        nexus_media_prefix = StringOption(
            default='/nexus/media/')
        nexus_use_django_media_url = BoolOption(
            default=False)
