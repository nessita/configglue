ConfigGlue
==========

![tests](https://github.com/nessita/confugglue/actions/workflows/tests.yml/badge.svg)


configglue -- glue for your apps' configuration

Three things:

AttributedConfigParser:

  a ConfigParser that gives you attributed options. So a config file with

    [foo]
    bar = Hello World
    bar.level = newbie

  will have one option under the 'foo' section, and that option will have a
  value ('Hello World') and an attribute 'level', with value 'newbie'.

TypedConfigParser:

  an AttributedConfigParser that uses the 'parser' attribtue to parse the
  value. So

    [foo]
    bar = 7
    bar.parser = int

  will have a 'foo' section with a 'bar' option which value is int('7').

configglue:

  A function that creates an TypedConfigParser and uses it to build an
  optparse.OptionParser instance. So you can have a config file with

    [foo]
    bar.default = 7
    bar.help = The bar number [%(default)s]
    bar.metavar = BAR
    bar.parser = int

  and if you load it with configglue, you get something like

    $ python sample.py --help
    Usage: sample.py [options]

    Options:
      -h, --help        show this help message and exit

      blah:
        --foo-bar=BAR   The bar number [7]
