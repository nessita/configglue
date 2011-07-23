###############################################################################
#
# configglue -- glue for your apps' configuration
#
# A library for simple, DRY configuration of applications
#
# (C) 2009--2011 by Canonical Ltd.
# by John R. Lenton <john.lenton@canonical.com>
# and Ricardo Kirkner <ricardo.kirkner@canonical.com>
#
# Released under the BSD License (see the file LICENSE)
#
# For bug reports, support, and new releases: http://launchpad.net/configglue
#
###############################################################################
import os
import user
from optparse import OptionParser
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
from configglue.schema import (
    IntOption,
    Schema,
)


def make_app(name=None, schema=None, plugin_manager=None, validate=False,
        parser=None):
    # patch sys.argv so that nose can be run with extra options
    # without conflicting with the schema validation
    # patch sys.stderr to prevent spurious output
    mock_sys = Mock()
    mock_sys.argv = ['foo.py']
    if validate:
        mock_sys.argv.append('--validate')
    with patch('configglue.glue.sys', mock_sys):
        with patch('configglue.app.base.sys.stderr'):
            app = App(name=name, schema=schema, plugin_manager=plugin_manager,
                parser=parser)
    return app


def make_config(app=None):
    if app is None:
        app = make_app()
    # patch sys.argv so that nose can be run with extra options
    # without conflicting with the schema validation
    mock_sys = Mock()
    mock_sys.argv = ['foo.py']
    with patch('configglue.glue.sys', mock_sys):
        config = Config(app)
    return config


class ConfigTestCase(TestCase):
    def get_xdg_config_dirs(self):
        xdg_config_home = os.environ.get('XDG_CONFIG_HOME',
            os.path.join(user.home, '.config'))
        xdg_config_dirs = ([xdg_config_home] + 
            os.environ.get('XDG_CONFIG_DIRS', '/etc/xdg').split(':'))
        return xdg_config_dirs

    @patch('configglue.app.base.merge')
    @patch('configglue.app.base.Config.get_config_files')
    @patch('configglue.app.base.configglue')
    def test_constructor(self, mock_configglue,
        mock_get_config_files, mock_merge):

        app = App()
        config = Config(app)

        self.assertEqual(config.schema, mock_merge.return_value)
        self.assertEqual(config.glue, mock_configglue.return_value)
        mock_configglue.assert_called_with(
            mock_merge.return_value, mock_get_config_files.return_value,
            op=app.parser)

    def test_glue_valid_config(self):
        config = make_config()
        self.assertEqual(config.glue.schema_parser.is_valid(), True)

    def test_glue_validate_invalid_config(self):
        class MySchema(Schema):
            foo = IntOption(fatal=True)

        self.assertRaises(SystemExit, make_app, schema=MySchema,
            validate=True)

    def test_glue_no_validate_invalid_config(self):
        class MySchema(Schema):
            foo = IntOption(fatal=True)
        # no explicit assertion as we just want to verify creating the
        # app doesn't raise any exception if validation is turned off
        make_app(schema=MySchema)

    def test_get_config_files(self):
        app = make_app()
        config = make_config(app=app)
        self.assertEqual(config.get_config_files(app), [])

    @patch('xdg.BaseDirectory.os.path.exists')
    def test_get_config_files_full_hierarchy(self, mock_path_exists):
        mock_path_exists.return_value = True

        config_files = []
        for path in reversed(self.get_xdg_config_dirs()):
            config_files.append(os.path.join(path, 'myapp', 'myapp.cfg'))
        config_files.append('./local.cfg')

        app = make_app(name='myapp')
        config = make_config(app=app)
        self.assertEqual(config.get_config_files(app=app), config_files)

    @patch('xdg.BaseDirectory.os.path.exists')
    def test_get_config_files_with_plugins_full_hierarchy(self,
        mock_path_exists):
        mock_path_exists.return_value = True

        class Foo(Plugin):
            enabled = True

        config_files = []
        for path in reversed(self.get_xdg_config_dirs()):
            config_files.append(os.path.join(path, 'myapp', 'myapp.cfg'))
            config_files.append(os.path.join(path, 'myapp', 'foo.cfg'))
        config_files.append('./local.cfg')

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

    def test_default_parser(self):
        app = make_app()
        # parser is configured
        self.assertNotEqual(app.parser, None)
        self.assertEqual(app.config.glue.option_parser, app.parser)
        # there is only one option by default: --validate
        self.assertEqual(app.parser.values.__dict__, {'validate': False})

    def test_custom_parser(self):
        custom_parser = OptionParser()
        custom_parser.add_option('-f', '--foo')
        app = make_app(parser=custom_parser)
        # parser is configured
        self.assertEqual(app.parser, custom_parser)
        self.assertEqual(app.config.glue.option_parser, custom_parser)
