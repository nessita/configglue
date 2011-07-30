=======================
Schema option reference
=======================

.. module:: configglue.schema
    :synopsis: Built-in options types.

.. currentmodule:: configglue

This document contains details about the `option attributes`_ and
`option types`_ included in configglue.

.. seealso::

    If the built-in options don't do the trick, you can easily
    :doc:`write your own custom schema options </howto/custom-schema-options>`. 

.. _common-schema-option-attributes:

Option attributes
=================

The following arguments are available to all option types. All are
*optional*.

``name``
--------

.. attribute:: Option.name

The name of the option. This will be automatically set to the name assigned to
the option in the schema definition.

``raw``
-------

.. attribute:: Option.raw

If ``True``, variable interpolation will not be carried out for this option.

Default is ``False``.

``default``
-----------

.. attribute:: Option.default

The default value for this option, if none is provided in the config file.

Default is ``configglue.schema.NO_DEFAULT``.

``fatal``
---------

.. attribute:: Option.fatal

If ``True``, ``SchemaConfigParser.parse_all`` will raise an exception if no
value is provided in the configuration file for this option. Otherwise,
``self.default`` will be used. 

Default is ``False``.

``help``
--------

.. attribute:: Option.help

The help text describing this option. This text will be used as the
``optparse.OptionParser`` help text.

Default is ``''``.

``section``
-----------

.. attribute:: Option.section

The :class:`~configglue.Section` object where this option was
defined.

Default is ``None``.

.. ``action``
..  ----------
..
..  .. attribute:: Option.action
..
..  lorem ipsum
.. 
..  Default is ``'store'``.

``short_name``
--------------

.. attribute:: Option.short_name

The short form name of the option. This will be used to set the short form
parameter of the ``optparse.OptionParser`` used for parsing the command line.

.. _schema-option-types:

Option types
============

.. currentmodule:: configglue.schema

``BoolOption``
--------------------

.. class:: BoolOption([**attributes])

A true/false option.

``IntOption``
-------------------

.. class:: IntOption([**attributes])

An integer.

``ListOption``
---------------------

.. class:: ListOption(item, [remove_duplicates=False, parse_json=True, **attributes])

A list of items.

.. attribute:: ListOption.item

    *Required*.

    List elements will be parsed as being of this type. Should be an
    instance of a subclass of :class:`~configglue.schema.Option`.

.. attribute:: ListOption.remove_duplicates

    *Optional*.

    If ``True``, duplicate elements will be removed from the parsed
    value.

.. attribute:: DictOption.parse_json

    .. versionadded:: 1.0

    *Optional*.

    The value for this option can be specified as a json string representing
    the list.

    Parsing will be attempted as if the value is a json string; if it fails,
    or the json string doesn't represent a list, the original semantics
    will be applied (ie, the value is interpreted as a newline-separated
    string).

    If ``False``, no attempt is made at trying to parse the value as a json
    string.

``StringOption``
----------------------

.. class:: StringOption([null=False, **attributes])

A string.

.. attribute:: StringOption.null

    *Optional*.

    If ``True``, a value of 'None' will be parsed into ``None``
    instead of just leaving it as the string 'None'.


``TupleOption``
---------------------

.. class:: TupleOption([length=0, **attributes])

A tuple of elements.

.. attribute:: TupleOption.length

    *Optional*.

    If not 0, the tuple has to have exactly this number of elements.

``DictOption``
--------------------

.. class:: DictOption([spec=None, strict=False, item=None, parse_json=True, **attributes])

A dictionary.

.. attribute:: DictOption.spec

    *Optional*.

    If not ``None``, should be a ``dict`` instance, such that its values
    are instances of a subclass of
    :class:`~configglue.schema.Option`.

.. attribute:: DictOption.strict

    *Optional*.

    If ``True``, no keys will be allowed other than those specified
    in the :attr:`~DictOption.spec`.

.. attribute:: DictOption.item

    *Optional*.

    Any not explicitly defined attributes will be parsed as being
    of this type. This should be an instance of a subclass of
    :class:`~configglue.schema.Option`.

.. attribute:: DictOption.parse_json

    .. versionadded:: 1.0

    *Optional*.

    The value for this option can be specified as a json string representing
    the dictionary.

    Parsing will be attempted as if the value is a json string; if it fails,
    or the json string doesn't represent a dictionary, the original semantics
    will be applied (ie, the value represents the name of a section defining
    the dictionary).

    If ``False``, no attempt is made at trying to parse the value as a json
    string.
