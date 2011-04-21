======================
configglue at a glance
======================

What is configglue?
===================

configglue is a library that glues together Python's optparse.OptionParser and
ConfigParser.ConfigParser, so that you don't have to repeat yourself when you
want to export the same options to a configuration file and a command-line
interface.

The main features of configglue are:

- ini-style configuration files
- schema-based configuration
- command-line integration
- configuration validation


Why would I want to use configglue?
===================================

Some of the benefits of using configglue are that it allows you to:

- separate configuration declaration (which options are available) from
  definition (what value does each option take)
- validate configuration files (there are no required options missing, prevent
  typos in option names, assert each option value is of the correct type)
- use standard types out of the box (integer, string, bool, tuple, list, dict)
- use standards-compatible configuration files (standard ini-files)
- create your own custom types beyond what's provided in the library 
- easily support command-line integration
- override options locally by using several configuration files (useful for
  separating configuration files for different environments)


Got curious?
============

You can find a quickstart guide for configglue on 
:doc:`quickstart` and you can get its code at
http://launchpad.net/configglue.

As an additional bonus, there is another project called 
django-configglue which allows you to use all the benefits of configglue on
your Django projects. You can find a quickstart guide for django-configglue on
http://packages.python.org/django-configglue and you can get its code at
http://launchpad.net/django-configglue.

