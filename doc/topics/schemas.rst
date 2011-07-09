=======
Schemas
=======

A schema is a static declaration of all your configuration settings. It
contains metadata about each setting so that the configuration can later
be validated.

The basics:

    * Each schema is a Python class that subclasses
      :class:`~configglue.pyschema.schema.Schema`.

    * Each attribute of the schema represents either a configuration section
      (see :class:`~configglue.pyschema.schema.Section`) or
      option (see :class:`~configglue.pyschema.schema.Option`).

Quick example
=============

This example schema defines the configuration for a database connection::

    from configglue import pyschema

    class DatabaseConnection(pyschema.Schema):
        host = pyschema.StringOption(
            default='localhost',
            help='Host where the database engine is listening on')
        port = pyschema.IntOption(
            default=5432,
            help='Port where the database engine is listening on')
        dbname = pyschema.StringOption(
            fatal=True,
            help='Name of the database to connect to')
        user = pyschema.StringOption(
            help='Username to use for the connection')
        password = pyschema.StringOption(
            help='Password to use fot the connection')

``host``, ``port``, ``dbname``, ``user`` and ``password`` are options_ of the
schema. Each option is specified as a class attribute.

Options
=======

The most important part of a schema is the list of configuration options it
defines. Options are specified by class attributes.

Example::

    class OvenSettings(pyschema.Schema):
        temperature = pyschema.IntOption()
        time = pyschema.IntOption()

Option types
------------

Each option in your schema should be an instance of the appropriate
:class:`~configglue.pyschema.schema.Option` class.

configglue ships with a couple of built-in option types; you can find the
complete list in the :ref:`schema option reference <schema-option-types>`. You
can easily write your own options if configglue's built-in ones don't do the
trick; see :doc:`/howto/custom-schema-options`.

Option attributes
-----------------

Each option takes a certain set of option-specific arguments (documented in
the :ref:`schema option reference <schema-option-types>`). For example,
:class:`~configglue.pyschema.schema.ListOption` (and its subclasses)
require a :attr:`~configglue.pyschema.schema.ListOption.item` argument
which specifies the type of the items contained in the list.

There's also a set of common arguments available to all option types. All are
optional. They're fully explained in the :ref:`reference
<common-schema-option-attributes>`, but here's a quick summary of the most
often-used ones:

    :attr:`~Option.default`
        The default value for this option, if none is provided in the config file.
        Default is :attr:`configglue.pyschema.schema.NO_DEFAULT`.

    :attr:`~Option.fatal`
        If ``True``, :func:`SchemaConfigParser.parse_all` will raise an exception if no
        value is provided in the configuration file for this option. Otherwise,
        :attr:`self.default` will be used. 
        Default is ``False``.

    :attr:`~Option.help`
        The help text describing this option. This text will be used as the
        :class:`optparse.OptParser` help text.
        Default is ``''``.

Again, these are just short descriptions of the most common option attributes.
Full details can be found in the :ref:`common schema option attribute reference <common-schema-option-attributes>`.

Option name restrictions
------------------------

configglue places only one restriction on schema option names:

    A option name cannot be a Python reserved word, because that would
    result in a Python syntax error. For example::

        class Example(pyschema.Schema):
            pass = pyschema.IntOption() # 'pass' is a reserved word!

Custom option types
-------------------

If one of the existing options cannot be used to fit your purposes, you can
create your own option class. Full coverage of creating your own options is
provided in :doc:`/howto/custom-schema-options`.

.. _schema-inheritance:

Schema inheritance
==================

Schema inheritance in configglue works almost identically to the way normal
class inheritance works in Python.

Section name "hiding"
---------------------

In normal Python class inheritance, it is permissible for a child class to
override any attribute from the parent class.

In order to allow easy extending of schemas, configglue overloads the standard
Python inheritance model. Whenever a schema is created, it will inherit all
its attributes from the base classes.

This poses a slight problem for attributes of type
:class:`~configglue.pyschema.schema.Section`. Usually, you'll want to
extend a :class:`~configglue.pyschema.schema.Section` instead of
overriding it. In order to achieve this, in your schema subclass, copy the
parent's attribute explicitely, to avoid modifying the parent schema class.
Option attributes (derived from
:class:`~configglue.pyschema.schema.Option`) will be overridden, as
expected.

For example::

    from copy import deepcopy

    from configglue import pyschema


    class BaseSchema(pyschema.Schema):
        option1 = pyschema.IntOption()

        class MySection(pyschema.Section):
            option1 = pyschema.BoolOption()


    class ChildSchema(BaseSchema):
        option2 = pyschema.IntOption()

        class MySection(BaseSchema.MySection):
            option2 = IntOption()

In this example :class:`ChildSchema` will have two top-level options,
:attr:`option1` and :attr:`option2`, and one section :attr:`MySection`, which
will have also two options within in (:attr:`MySection.option1` and
:attr:`MySection.option2`). So, defining :class:`ChildSchema` in this way
produces the same result as explicitely describing each attribute, as
expected::

    from configglue import pyschema

    class ChildSchema(pyschema.Schema):
        option1 = pyschema.IntOption()
        option2 = pyschema.IntOption()

        class MySection(pyschema.Section):
            option1 = pyschema.BoolOption()
            option2 = IntOption()


Multiple inheritance
--------------------

Just as with Python's subclassing, it's possible for a configglue schema to
inherit from multiple parent schemas. Keep in mind that normal Python name
resolution rules apply.

Generally, you won't need to inherit from multiple parents. The main use-case
where this is useful is for "mix-in" classes: adding a particular extra option
to every class that inherits the mix-in. Try to keep your inheritance
hierarchies as simple and straightforward as possible so that you won't have
to struggle to work out where a particular piece of information is coming
from.
