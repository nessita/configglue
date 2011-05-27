import user
from ConfigParser import NoSectionError
from unittest import TestCase

from mock import (
    Mock,
    patch,
)

from configglue.app.base import App
from configglue.pyschema import (
    IntConfigOption,
    Schema,
)


class AppTestCase(TestCase):
    def make_app(self, schema=None, name=None):
        if schema is None:
            schema = Schema
        # patch sys.argv so that nose can be run with extra options
        # without conflicting with the schema validation
        mock_sys = Mock()
        mock_sys.argv = ['foo.py']
        with patch('configglue.pyschema.glue.sys', mock_sys):
            app = App(schema, name=name)
        return app

    def test_name_from_constructor(self):
        app = self.make_app(name='myapp')
        self.assertEqual(app.name, 'myapp')

    @patch('configglue.app.base.sys')
    def test_name_from_script(self, mock_sys):
        mock_sys.argv = ['foo.py']
        app = self.make_app()
        self.assertEqual(app.name, 'foo')

    def test_get_config_files(self):
        app = self.make_app()
        self.assertEqual(app.get_config_files(), [])

    @patch('xdg.BaseDirectory.os.path.exists')
    def test_get_config_files_full_hierarchy(self, mock_path_exists):
        mock_path_exists.return_value = True
        config_files = [
            '/etc/xdg/myapp/config.ini',
            '/etc/xdg/xdg-gnome/myapp/config.ini',
            "{0}/.config/myapp/config.ini".format(user.home),
            'config.ini',
        ]
        app = self.make_app(name='myapp')
        self.assertEqual(app.get_config_files(), config_files)

    def test_glue_valid_config(self):
        app = self.make_app()
        self.assertNotEqual(app.glue.schema_parser.schema, Schema)
        self.assertEqual(app.glue.schema_parser.is_valid(), True)

    def test_glue_invalid_config(self):
        class MySchema(Schema):
            foo = IntConfigOption(fatal=True)
        self.assertRaises(NoSectionError, self.make_app, schema=MySchema)

