from configglue.pyschema import Schema


__all__ = [
    'Plugin',
    'PluginManager',
]


class Plugin(object):
    schema = Schema
    enabled = False


class PluginManager(object):
    def __init__(self):
        self.available = self.load()

    @property
    def enabled(self):
        return set((cls for cls in self.available if cls.enabled))

    def enable(self, plugin):
        plugin.enabled = True

    def disable(self, plugin):
        plugin.enabled = False

    @property
    def schemas(self):
        return [cls.schema for cls in self.enabled]

    def load(self):
        return set()

    def register(self, plugin):
        self.available.add(plugin)
