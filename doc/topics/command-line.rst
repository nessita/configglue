================
The command-line
================

One of the nicest things about configglue is its ability to easily integrate
the command line for specifying or overriding configuration values.

In the example given in the :doc:`quickstart guide </intro/quickstart>`, it
can be seen how the command line is used to supply the value of a
configuration option.

Top-level configuration options are matched using the simple
::

    --option=value

syntax.

Options that are within a section will be matched using the compound
::

    --section_option=value

syntax; therefore it's not possible to have a section or option name contain
underscore characters, as they would clash with the command line argument name
resolution method.

Short-form names
================

If the :class:`~configglue.schema.Option` has a non-empty
:attr:`~configglue.schema.Option.short_name` set, this will be used as the
short-form name for the command line parameter. For example, given the
schema ::

    class MySchema(schema.Schema):
        foo = IntOption(short_name='f')

the following forms of specifying a value for this option are equivalent::

    --foo=1

and
::

    -f 1

Environment variables
=====================

Environment variables can be used for overriding configuration options. For
more information, see the documentation about
:ref:`environment-variables-command-line`.
