from configglue.schema import Schema, Section, StringOption


class SentrySchema(Schema):
    class sentry(Section):
        sentry_dsn = StringOption()
