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
