===================
Configuration files
===================

configglue uses standard INI-style configuration files to store the values for
the configuration, in the same format supported by ConfigParser. Within a
configuration file, there a few special syntax constructs you should be aware of. 

A Section is matched by a ConfigParser section, which is defined like::

    [MySection]

A Option is matched by a ConfigParser option, which is defined by a
simple key, value pair, like::

    my_option = the value

So, a very simple configuration file could look like::

    [MySection]
    my_option = the value

This configuration file would match with a schema like the following::

    class MySchema(schema.Schema):
        class MySection(schema.Section):
            my_option = schema.StringOption()

======================
Special considerations
======================

There is always an implicitely defined section called ``__main__``
==================================================================

A few special considerations have to be kept in mind while working with these
configuration files. As ConfigParser requires a config file to have at least
one section defined, any top-level Options are added to an implicitely
defined section called ``__main__``.

Therefore, if you have a schema like::

    class MySchema(schema.Schema):
        foo = IntOption()

and you want to write a configuration file to match it, it would have to look
like::

    [__main__]
    foo = 42


Specifying configuration values for basic data types
====================================================

For any basic data types, such as strings, numbers and booleans, specifying
those in your configuration files is trivial; you just have to write them down
as `key = value` pairs.

Specifying more complex data
============================

For more advanced data types, such as lists, tuples or dictionaries there are
a few syntactic conventions you should be aware of.

Tuples
------

For specifying the value of a :class:`~configglue.schema.TupleOption`,
you just put all the values in the same line, separated by `,`, as shown::

    my_tuple = 1, 2, 3

This will be parsed as the tuple `(1, 2, 3)`.

Lists
-----

For specifying the value of a :class:`~configglue.schema.ListOption`,
you just put each value on a different line, as shown::

    my_list = 1
              2
              3

This will be parsed as the list `[1, 2, 3]`.

Dictionaries
------------

For specifying the value of a :class:`~configglue.schema.DictOption`,
a special syntax convention was defined. The value of a 
:class:`~configglue.schema.DictOption` is the name of a section
describing the structure of that dictionary.

For example, given the configuration file::

    my_dict = my_dict_sect

    [my_dict_sect]
    foo = 1
    bar = true

and the schema::

    class MySchema(schema.Schema):
        my_dict = schema.DictOption(
            spec={'foo': schema.IntOption(),
                  'bar': schema.BoolOption()})

`my_dict` would be parsed as::

    {'foo': 1, 'bar': True}


Environment variables
=====================

You can also specify the value in the configuration file as an expression
involving environment variables.

For more details, refer to the documentation about
:ref:`environment-variables-config-file`.
