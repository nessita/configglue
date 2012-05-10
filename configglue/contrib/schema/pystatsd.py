from configglue.schema import IntOption, Schema, Section, StringOption


class PyStatsdSchema(Schema):
    """Configglue schema for pystatsd."""

    __version__ = '0.1.6'

    class statsd(Section):
        statsd_host = StringOption(
            default='localhost')
        statsd_port = IntOption(
            default=8125)
