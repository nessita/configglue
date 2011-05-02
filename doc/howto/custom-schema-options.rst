===========================
Writing custom option types
===========================

.. currentmodule:: configglue.pyschema.schema

Introduction
============

The :doc:`schema reference </topics/schemas>` documentation explains how to
use configglue's standard option classes --
:class:`~configglue.pyschema.schema.BoolConfigOption`,
:class:`~configglue.pyschema.schema.IntConfigOption`, etc. For many purposes,
those classes are all you'll need. Sometimes, though, the configglue version
won't meet your precise requirements, or you'll want to use a option that is
entirely different from those shipped with configglue.

configglue's built-in option types don't cover every possible data type --
only the common types, such as ``bool`` and ``int``. For more obscure data
types, such as complex numbers or even user-created types you can define your
own configglue :class:`~configglue.pyschema.schema.ConfigOption` subclasses.

Writing an option subclass
==========================

When planning your :class:`~configglue.pyschema.schema.ConfigOption` subclass,
first give some thought to which existing
:class:`~configglue.pyschema.schema.ConfigOption` class your new option
is most similar to. Can you subclass an existing configglue option and save
yourself some work? If not, you should subclass the
:class:`~configglue.pyschema.schema.ConfigOption` class, from which everything
is descended.

Initializing your new option is a matter of separating out any arguments that are
specific to your case from the common arguments and passing the latter to the
:meth:`~configglue.pyschema.schema.ConfigOption.__init__` method of
:class:`~configglue.pyschema.schema.ConfigOption` (or your parent class).

In our example, we'll call our option ``UpperCaseDictConfigOption``. (It's a
good idea to call your :class:`~configglue.pyschema.schema.ConfigOption`
subclass ``<Something>ConfigOption``, so it's easily identifiable as a
:class:`~configglue.pyschema.schema.ConfigOption` subclass.) It behaves
mostly like a :class:`~configglue.pyschema.schema.DictConfigOption`, so we'll
subclass from that::

    from configglue import pyschema

    class UpperCaseDictConfigOption(pyschema.DictConfigOption):
        """ A DictConfigOption with all upper-case keys. """

        def parse(self, section, parser=None, raw=False):
            parsed = super(UpperCaseDictConfigOption, self).parse(
                section, parser, raw)
            result = {}
            for k, v in parsed.items():
                result[k.upper()] = v
            return result


Our ``UpperCaseDictConfigOption`` will represent a dictionary with all-uppercase
keys.

So, let's assume we have a configuration file (see documentation on 
:doc:`configuration files </topics/config-file>` for details) that includes::

    [__main__]
    mydict = mydict_section

    [mydict_section]
    foo = 1
    bar = 2

and a schema like::

    class MySchema(pyschema.Schema):
        mydict = UpperCaseDictConfigOption()

When parsing this configuration file, the parser will contain the following
value for the ``mydict`` attribute::

    {'FOO': '1', 'BAR': '2'}

.. note::
    Note that the dictionary values are strings because we didn't specify an
    item type for the ``UpperCaseDictConfigOption``, and so it defaulted to
    :class:`~configglue.pyschema.schema.StringConfigOption`.

