###############################################################################
#
# configglue -- glue for your apps' configuration
#
# A library for simple, DRY configuration of applications
#
# (C) 2009--2013 by Canonical Ltd.
# by John R. Lenton <john.lenton@canonical.com>
# and Ricardo Kirkner <ricardo.kirkner@canonical.com>
#
# Released under the BSD License (see the file LICENSE)
#
# For bug reports, support, and new releases: http://launchpad.net/configglue
#
###############################################################################
from configglue.schema import (
    ListOption,
    Schema,
    Section,
    StringOption,
    TupleOption,
    )


class DjangoJenkinsSchema(Schema):
    """Configglue schema for django-jenkins."""

    __version__ = '0.12.1'

    class django_jenkins(Section):
        project_apps = ListOption(
            item=StringOption(),
            default=[],
            help='List of of django apps for Jenkins to run.')
        jenkins_tasks = TupleOption(
            default=(
                'django_jenkins.tasks.run_pylint',
                'django_jenkins.tasks.with_coverage',
                'django_jenkins.tasks.django_tests',
            ),
            help='List of Jenkins tasks executed by ./manage.py jenkins '
                'command.')
        jenkins_test_runner = StringOption(
            default='',
            help='The name of the class to use for starting the test suite for '
                'jenkins and jtest commands. Class should be inherited from '
                'django_jenkins.runner.CITestSuiteRunner.')
