=======================================
Writing configglue-enabled applications
=======================================

By inheriting from :class:`~configglue.app.App`, your application will
reap the benefits of being able to

Read configuration files from standard locations
================================================

The configglue-enabled app will automatically follow the XDG_ standards for
looking up configuration files. For example, if your application is named
*myapp*, the following locations will be searched for configuration values::

    /etc/xdg/myapp/myapp.cfg
    /home/<user>/.config/myapp/myapp.cfg
    ./local.cfg

Support plugins for extending your application
==============================================

The class :class:`~configglue.app.Plugin` will allow you to write plugins for
your application so that each plugin can have it's own configglue-based
configuration.

Each plugin registered with the application will have it's own schema and
configuration files, which will be included during validation. If the plugin
is named *myplugin*, the following additional locations will be searched for
configuration values::

    /etc/xdg/myapp/myplugin.cfg
    /home/<user>/.config/myapp/myplugin.cfg

Plugins need to be registered with the application manually for the time
being. For doing so, just call :meth:`~configglue.app.App.plugins.register`,
like::

    class FooSchema(Schema):
        bar = IntOption()

    class Foo(Plugin):
        enabled = True
        schema = FooSchema

    myapp = App(name='myapp')
    myapp.plugins.register(Foo)

This example will register a `Foo` plugin which will be enabled by default.

Plugins can be enabled/disabled on demand, by calling the respective method
::

    >>> myapp.plugins.enable(Foo)
    >>> print myapp.plugins.enabled
    [<class 'Foo'>]

    >>> myapp.plugins.disable(Foo)
    >>> print myapp.plugins.enabled
    []

The list of available plugins can be retrieved like
::

    >>> print myapp.plugins.available
    [<class 'Foo'>]


.. _XDG: http://www.freedesktop.org/wiki/Specifications/basedir-spec

Nicely integrate with the command line
======================================

By extending the :class:`~configglue.app.App` class, your program
automatically has nice command line integration support built-in.

Getting help
------------

In order to show a help message, with information about each option your
program supports, you can invoke it like::

    python myapp.py --help

and it will output something similar to
::

    Usage: myapp.py [options]

    Options:
      -h, --help  show this help message and exit
      --validate  validate configuration

Validating the configuration
----------------------------

If invoked with the *--validate* option, the configuration will be validated,
producing one of two possible outcomes.

If no errors are found in the configuration, there will be no output, and your
program will exit with a successful status code (0).

If errors are found during validation, those will be shown on the standard
output, and your program will exit with an error status code (1).


Customizing the supported options
---------------------------------

If you want to customize the options your program will support in the command
line, beyond those already included by introspecting the schema, you can do so
by initializing your application with an instance of
:class:`optparse.OptionParser`.

For example, imagine your application code looks like::

    class MySchema(schema.Schema):
        foo = schema.IntOption()

    parser = OptionParser()
    parser.add_option('-b', '--bar')
    app = app.App(MySchema, parser=parser)

when invoking the help you'd get
::

    Usage: myapp.py [options]

    Options:
        -h, --help         show this help message and exit
        -b BAR, --bar=BAR
        --foo=FOO

.. note:: If you override the option parser, you will not get the default
    options set. You will have to include them yourself, if so desired.

.. note:: In order to trigger configuration validation, the only requirement
    is that the option parser includes a boolean option called *validate*.
