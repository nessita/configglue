from configglue.schema import IntOption, Schema, Section, StringOption


class StatsdSchema(Schema):
    class statsd(Section):
        statsd_host = StringOption(default='localhost')
        statsd_port = IntOption(default=8125)
