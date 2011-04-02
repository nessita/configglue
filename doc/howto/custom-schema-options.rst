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
own configglue ``ConfigOption`` subclasses.

TBD
