=======================
Schema option reference
=======================

.. module:: configglue.pyschema.schema
    :synopsis: Built-in options types.

.. currentmodule:: configglue.pyschema

This document contains details about the `option attributes`_ and
`option types`_ included in configglue.

.. seealso::

    If the built-in options don't do the trick, you can easily
    :doc:`write your own custom schema options </howto/custom-schema-options>`. 

.. note::

    Technically, these classes are defined in
    :mod:`configglue.pyschema.schema`, but for convenience they're imported
    into :mod:`configglue.pyschema`; the standard convention is to use
    ``from configglue import pyschema`` and refer to classes as
    ``pyschema.<Foo>ConfigOption``.

.. _common-schema-option-attributes:

Option attributes
=================

The following arguments are available to all option types. All are
*optional*.

``name``
--------

.. attribute:: ConfigOption.name

The name of the option. This will be automatically set to the name assigned to
the option in the schema definition.

``raw``
-------

.. attribute:: ConfigOption.raw

If ``True``, variable interpolation will not be carried out for this option.

Default is ``False``.

``default``
-----------

.. attribute:: ConfigOption.default

The default value for this option, if none is provided in the config file.

Default is ``configglue.pyschema.schema.NO_DEFAULT``.

``fatal``
---------

.. attribute:: ConfigOption.fatal

If ``True``, ``SchemaConfigParser.parse_all`` will raise an exception if no
value is provided in the configuration file for this option. Otherwise,
``self.default`` will be used. 

Default is ``False``.

``help``
--------

.. attribute:: ConfigOption.help

The help text describing this option. This text will be used as the
``optparse.OptParser`` help text.

Default is ``''``.

``section``
-----------

.. attribute:: ConfigOption.section

The :class:`~configglue.pyschema.ConfigSection` object where this option was
defined.

Default is ``None``.

.. ``action``
..  ----------
..
..  .. attribute:: ConfigOption.action
..
..  lorem ipsum
.. 
..  Default is ``'store'``.

.. _schema-option-types:

Option types
============

.. currentmodule:: configglue.pyschema.schema

``BoolOption``
--------------------

.. class:: BoolOption([**attributes])

A true/false option.

``IntOption``
-------------------

.. class:: IntOption([**attributes])

An integer.

``LinesConfigOption``
---------------------

.. class:: LinesConfigOption(item, [remove_duplicates=False, **attributes])

A list of items.

.. attribute:: LinesConfigOption.item

    *Required*.

    List elements will be parsed as being of this type. Should be an
    instance of a subclass of :class:`~configglue.pyschema.schema.ConfigOption`.

.. attribute:: LinesConfigOption.remove_duplicates

    *Optional*.

    If ``True``, duplicate elements will be removed from the parsed
    value.

``StringOption``
----------------------

.. class:: StringOption([null=False, **attributes])

A string.

.. attribute:: StringOption.null

    *Optional*.

    If ``True``, a value of 'None' will be parsed into ``None``
    instead of just leaving it as the string 'None'.


``TupleConfigOption``
---------------------

.. class:: TupleConfigOption([length=0, **attributes])

A tuple of elements.

.. attribute:: TupleConfigOption.length

    *Optional*.

    If not 0, the tuple has to have exactly this number of elements.

``DictConfigOption``
--------------------

.. class:: DictConfigOption([spec=None, strict=False, item=None, **attributes])

A dictionary.

.. attribute:: DictConfigOption.spec

    *Optional*.

    If not ``None``, should be a ``dict`` instance, such that its values
    are instances of a subclass of
    :class:`~configglue.pyschema.schema.ConfigOption`.

.. attribute:: DictConfigOption.strict

    *Optional*.

    If ``True``, no keys will be allowed other than those specified
    in the :attr:`~DictConfigOption.spec`.

.. attribute:: DictConfigOption.item

    *Optional*.

    Any not explicitly defined attributes will be parsed as being
    of this type. This should be an instance of a subclass of
    :class:`~configglue.pyschema.schema.ConfigOption`.

