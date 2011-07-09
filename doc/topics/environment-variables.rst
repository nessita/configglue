=====================
Environment variables
=====================

Environment variables are now supported in two flavours

.. _environment-variables-command-line:

Environment variables during command-line integration
=====================================================

If an environment variable of the form

CONFIGGLUE_FOO_BAR is defined, it will be used to override the configuration
value for option foo in section bar, according to the following precedence
rules:

1. Explicitly defined via command-line (i.e, --section_option=value)
2. Implicitly defined via environment variable (i.e, CONFIGGLUE_SECTION_OPTION)
3. Explicitly defined via configuration files
4. Implicitly defined via schema defaults

To illustrate, a few examples. Given the example from the :doc:`quickstart
guide </intro/quickstart>`, the following examples illustrate the precedence
rules just mentioned.

Implicitly defined via schema defaults
::

    $ python app.py
    foo option has default value: 0
    bar option has default value: False

Implicitly defined via environment variable (overriding schema defaults)
::

    $ CONFIGGLUE_FOO=3 python app.py
    foo option has been configured with value: 3
    bar option has default value: False

Explicitly defined via command-line
::

    $ CONFIGGLUE_FOO=3 python app.py --foo=2
    foo option has been configured with value: 2
    bar option has default value: False

Explicitly defined via configuration files
::

    $ echo "[__main__]\nfoo = 5" > config.ini
    $ python app.py
    foo option has been configured with value: 5
    bar option has default value: False

Implicitly defined via environment variable (overriding config file)
::

    $ CONFIGGLUE_FOO=33 python app.py
    foo option has been configured with value: 33
    bar option has default value: False


.. _environment-variables-config-file:

Environment variables as placeholders in configuration files
============================================================

In the configuration files, if an option has a value such as

$FOO

or

${FOO}

it will be interpolated using the FOO environment variable, or if that
variable is not defined, it will fallback to the default value for that
option.

Using the same example as shown in the :doc:`quickstart guide
</intro/quickstart>`, this use case can be illustrated as follows.

Specifying a value in the configuration file using an environment variable
::

    $ echo "[__main__]\nfoo = \$BAZ" > config.ini
    $ BAZ=33 python app.py
    foo option has been configured with value: 33

If the environment variable is not defined, fallback to the default value
::

    $ python app.py
    foo option has default value: 0
