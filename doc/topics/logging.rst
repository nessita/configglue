=======
Logging
=======

configglue uses its own loggers to allow library users to define the desired
verbosity.

Existing loggers exposed by configglue are:

  * configglue.parser

To enable logging you need to configure the system like
::

    logging.dictConfig({
        'loggers': {
            'configglue.parser': {
                'handlers': ['console'],
                'level': 'WARNING',
                },
            },
        'handlers': {
            'console': {
                'formatter': 'simple',
                'class': 'logging.handlers.StreamHandler',
                'level': 'WARNING'
                'args': (sys.stdout,)
                },
            },
        'formatters': {
            'simple': {
                'format': '%(levelname)s %(message)s'
                }
            },
        })
