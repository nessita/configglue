================
Plugin reference
================

.. module:: configglue.app.plugin
    :synopsis: Base classes for plugins and plugin managers.

.. currentmodule:: configglue.app

This document contains details about the base classes provided by configglue
for writing plugins and plugin managers.

``Plugin``
----------

.. class:: Plugin()

This is the base class from which your plugins should inherit in order to
integrate with your configglue-enabled application.

.. attribute:: Plugin.schema

    This is the schema class describing any configuration specific to your
    plugin.

    By default a standard :class:`~configglue.schema.Schema` is used.

.. attribute:: Plugin.enabled

    Whether the plugin is enabled.

    By default new plugins are *disabled*.


``PluginManager``
-----------------

.. class:: PluginManager()

This is the base class from which any custom plugin managers should inherit.

.. attribute:: PluginManager.available

    The list of currently available plugin classes.

.. attribute:: PluginManager.enabled

    The list of currently enabled plugin classes.

.. attribute:: PluginManager.schemas

    The list of schemas for the currently enabled plugins.

.. method:: PluginManager.enable(plugin)

    Enable the plugin.

    *plugin* is the plugin *class*.

.. method:: PluginManager.disable(plugin)

    Disable the plugin.

    *plugin* is the plugin *class*.

.. method:: PluginManager.register(plugin)

    Register the plugin by adding it to the list of available plugins.

    *plugin* is the plugin *class*.

.. method:: PluginManager.load()

    Load plugins.

    Return the list of classes for the loaded plugins.
