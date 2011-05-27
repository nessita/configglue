import os.path
import sys

from xdg.BaseDirectory import load_config_paths
from xdgapp import XdgApplication

from configglue.pyschema import configglue


class App(XdgApplication):
    def __init__(self, schema, name=None, create_dirs=True):
        # initialize app name
        if name is None:
            name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        self.name = name

        super(App, self).__init__(name, create_dirs)

        # initialize config
        config_files = self.get_config_files()
        self.glue = configglue(schema, config_files)

    def get_config_files(self):
        config_files = []
        for path in reversed(list(load_config_paths(self.app))):
            config_files.append(os.path.join(path, 'config.ini'))
        if os.path.exists('config.ini'):
            config_files.append('config.ini')
        return config_files

