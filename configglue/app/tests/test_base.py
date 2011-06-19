import user
from ConfigParser import NoOptionError
from unittest import TestCase

from mock import (
    Mock,
    patch,
)

from configglue.app.base import (
    App,
    Config,
)
from configglue.app.plugin import (
    Plugin,
    PluginManager,
)
from configglue.pyschema import (
    IntOption,
    Schema,
)


def make_app(name=None, schema=None, plugin_manager=None):
    # patch sys.argv so that nose can be run with extra options
    # without conflicting with the schema validation
    mock_sys = Mock()
    mock_sys.argv = ['foo.py']
    with patch('configglue.pyschema.glue.sys', mock_sys):
        app = App(name=name, schema=schema, plugin_manager=plugin_manager)
    return app


def make_config(app=None):
    if app is None:
        app = make_app()
    # patch sys.argv so that nose can be run with extra options
    # without conflicting with the schema validation
    mock_sys = Mock()
    mock_sys.argv = ['foo.py']
    with patch('configglue.pyschema.glue.sys', mock_sys):
        config = Config(app)
    return config


class ConfigTestCase(TestCase):
    @patch('configglue.app.base.merge')
    @patch('configglue.app.base.Config.get_config_files')
    @patch('configglue.app.base.configglue')
    def test_constructor(self, mock_configglue,
        mock_get_config_files, mock_merge):

        config = Config(App())

        self.assertEqual(config.schema, mock_merge.return_value)
        self.assertEqual(config.glue, mock_configglue.return_value)
        mock_configglue.assert_called_with(
            mock_merge.return_value, mock_get_config_files.return_value)

    def test_glue_valid_config(self):
        config = make_config()
        self.assertEqual(config.glue.schema_parser.is_valid(), True)

    def test_glue_invalid_config(self):
        class MySchema(Schema):
            foo = IntOption(fatal=True)
        self.assertRaises(SystemExit, make_app, schema=MySchema)

    def test_get_config_files(self):
        app = make_app()
        config = make_config(app=app)
        self.assertEqual(config.get_config_files(app), [])

    @patch('xdg.BaseDirectory.os.path.exists')
    def test_get_config_files_full_hierarchy(self, mock_path_exists):
        mock_path_exists.return_value = True
        config_files = [
            '/etc/xdg/myapp/myapp.cfg',
            '/etc/xdg/xdg-gnome/myapp/myapp.cfg',
            "{0}/.config/myapp/myapp.cfg".format(user.home),
            './local.cfg',
        ]
        app = make_app(name='myapp')
        config = make_config(app=app)
        self.assertEqual(config.get_config_files(app=app), config_files)

    @patch('xdg.BaseDirectory.os.path.exists')
    def test_get_config_files_with_plugins_full_hierarchy(self,
        mock_path_exists):
        mock_path_exists.return_value = True

        class Foo(Plugin):
            enabled = True

        config_files = [
            '/etc/xdg/myapp/myapp.cfg',
            '/etc/xdg/myapp/foo.cfg',
            '/etc/xdg/xdg-gnome/myapp/myapp.cfg',
            '/etc/xdg/xdg-gnome/myapp/foo.cfg',
            "{0}/.config/myapp/myapp.cfg".format(user.home),
            "{0}/.config/myapp/foo.cfg".format(user.home),
            './local.cfg',
        ]
        app = make_app(name='myapp')
        app.plugins.register(Foo)
        config = make_config(app=app)
        self.assertEqual(config.get_config_files(app=app), config_files)


class AppTestCase(TestCase):
    def test_custom_name(self):
        app = make_app(name='myapp')
        self.assertEqual(app.name, 'myapp')

    @patch('configglue.app.base.sys')
    def test_default_name(self, mock_sys):
        mock_sys.argv = ['foo.py']
        app = make_app()
        self.assertEqual(app.name, 'foo')

    def test_default_plugin_manager(self):
        app = make_app()
        self.assertEqual(type(app.plugins), PluginManager)

    def test_custom_plugin_manager(self):
        mock_plugin_manager = Mock()
        mock_plugin_manager.schemas = []
        app = make_app(plugin_manager=mock_plugin_manager)
        self.assertEqual(app.plugins, mock_plugin_manager)

    @patch('configglue.app.base.Config')
    def test_config(self, mock_config):
        app = make_app()
        self.assertEqual(app.config, mock_config.return_value)
