================================
Application base class reference
================================

.. module:: configglue.app.base
    :synopsis: Base class for configglue-enabled application.

.. currentmodule:: configglue.app

This document contains details about the base class provided by configglue
for writing configglue-enabled applications.

``App``
-------

.. class:: App([schema=None, plugin_manager=None, name=None, create_dirs=True])

This is the base class from which your application should inherit in order to
easily integrate itself with configglue.

More details about what kind of benefits this provides are depicted in the
introduction to
:doc:`writing configglue-enabled applications </topics/base-app>`.

.. attribute:: App.schema

    *Optional*.

    This is the schema class for the application. This schema should describe
    application-wide configuration.

    The schema can also be specified as a class attribute of subclasses of
    :class:`~configglue.app.App`.

.. attribute:: App.plugin_manager

    *Optional*.

    This is the class used to manage plugins. Should be an subclass of
    :class:`~configglue.app.plugin.PluginManager`.

    The default :class:`~configglue.app.plugin.PluginManager` will be used if
    none is specified.

    The plugin manager can also be specified as a class attribute of subclasses of
    :class:`~configglue.app.App`.

.. attribute:: App.name

    *Optional*.

    The name of the application. This value will be used to determine where to
    look for configuration files.

    If none is provided, the application will take the name of the script used
    to invoke it from the command line.

.. attribute:: App.create_dirs

    *Optional*.

    If ``False``, directories where configuration files are looked for will
    not get created if they don't exist.

    The default is to create non-existant directories.


