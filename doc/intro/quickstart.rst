=================================================
Writing your first configglue-enabled application
=================================================

This is a minimalistic step-by-step guide on how to start using configglue to
manage configuration settings for your application.

Jump right in
=============

Most of the time the code needed to make your application work with configglue
will look like the following snippet, so let's look at it in detail::

    def main(config, opts):
        # do something
        values = config.values('__main__')
        for opt in ('foo', 'bar'):
            option = config.schema.section('__main__').option(opt)
            value = values.get(opt)
            if value != option.default:
                print "%s option has been configured with value: %s" % (opt,
                    value)
            else:
                print "%s option has default value: %s" % (opt, option.default)

    if __name__ == '__main__':
        from configglue import pyschema

        # create the schema
        class MySchema(pyschema.Schema):
            foo = pyschema.IntOption()
            bar = pyschema.BoolOption()

        # read the configuration files
        scp = pyschema.SchemaConfigParser(MySchema())
        scp.read(['config.ini'])

        # support command-line integration
        op, opts, args = pyschema.schemaconfigglue(scp)

        # validate the config (after taking into account any command-line
        # provided options
        is_valid, reasons = scp.is_valid(report=True)
        if not is_valid:
            op.error(reasons[0])

        # run
        main(scp, opts)

Let's start at the top.

You'll probably have a *main* function that you'll be calling to get
your application started.

::

    def main(config, opts):
        # do something
        ...

    if __name__ == '__main__':
        ...
        # run
        main(scp, opts)

So, for configglue to deliver it's awesomeness, all the magic has to happen
before calling your *main* function.

The general structure is:

#. Create a schema for your configuration

    ::

        class MySchema(pyschema.Schema):
            foo = pyschema.IntOption()
            bar = pyschema.BoolOption()

#. Create a parser for that schema

    ::

        scp = pyschema.SchemaConfigParser(MySchema())

#. Read the configuration files (to get the statically defined configuration
   values)

    ::

        scp.read(['config.ini'])

#. (Optional) Weave in command-line integration support (so that configuration
   options can be overridden via command-line)

    ::

        op, opts, args = pyschema.schemaconfigglue(scp)

#. (Optional) Validate the effective configuration (to capture any
   configuration issues)

    ::

        is_valid, reasons = scp.is_valid(report=True)
        if not is_valid:
            op.error(reasons[0])

Since this code will be structured the same for any configglue-enabled project
you do, there is also a utility function you can use to avoid repeating
yourself.

When using that function (see :func:`configglue.pyschema.glue.configglue`),
this code would look like::

    def main(config, opts):
        # do something
        values = config.values('__main__')
        for opt in ('foo', 'bar'):
            option = config.schema.section('__main__').option(opt)
            value = values.get(opt)
            if value != option.default:
                print "%s option has been configured with value: %s" % (opt,
                    value)
            else:
                print "%s option has default value: %s" % (opt, option.default)

    if __name__ == '__main__':
        from configglue import pyschema

        # create the schema
        class MySchema(pyschema.Schema):
            foo = pyschema.IntOption()
            bar = pyschema.BoolOption()

        # glue everything together
        glue = pyschema.configglue(MySchema, ['config.ini'])

        # run
        main(glue.schema_parser, glue.options)


Test it
=======

To test our configglue support, let's try out different use cases.

#. Default values

    ::

        $ python app.py
        foo option has default value: 0
        bar option has default value: False

#. Config file

    Write the following content to a file called *config.ini*::

        [__main__]
        bar = true

    and then run

    ::

        $ python app.py
        foo option has default value: 0
        bar option has been configured with value: True

#. Command-line integration

    ::

        $ python app.py --foo=2
        foo option has been configured with value: 2
        bar option has been configured with value: True

    .. note:: This output is assuming you still have the *config.ini* file you
        created during the previous use case.


Profit!
=======

That's it! Your application now uses configglue to manage it's configuration.
Congratulations!

