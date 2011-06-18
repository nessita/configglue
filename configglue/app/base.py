import os.path
import sys

from xdg.BaseDirectory import load_config_paths
from xdgapp import XdgApplication

from configglue.pyschema import (
    Schema,
    configglue,
    merge,
)
from .plugin import PluginManager


__all__ = [
    'App',
]


class Config(object):
    def __init__(self, app):
        schemas = [app.schema] + app.plugins.schemas
        self.schema = merge(*schemas)

        # initialize config
        config_files = self.get_config_files(app)
        self.glue = configglue(self.schema, config_files)

    def get_config_files(self, app):
        config_files = []
        for path in reversed(list(load_config_paths(app.name))):
            self._add_config_file(config_files, path, app.name)
            for plugin in app.plugins.enabled:
                self._add_config_file(config_files, path, plugin.__name__)
        self._add_config_file(config_files, '.', 'local')
        return config_files

    def _add_config_file(self, config_files, path, name):
        filename = os.path.join(path, "{0}.cfg".format(name.lower()))
        if os.path.exists(filename):
            config_files.append(filename)


class App(XdgApplication):
    schema = Schema
    plugin_manager = PluginManager

    def __init__(self, schema=None, plugin_manager=None, name=None,
        create_dirs=True):
        # initialize app name
        if name is None:
            name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        self.name = name

        super(App, self).__init__(name, create_dirs)

        # setup plugins
        if plugin_manager is None:
            self.plugins = self.plugin_manager()
        else:
            self.plugins = plugin_manager
        # setup config
        if schema is not None:
            self.schema = schema
        self.config = Config(self)
