from configglue.schema import (
    ListOption,
    Schema,
    Section,
    StringOption,
    TupleOption,
    )


class DjangoJenkinsSchema(Schema):
    class django_jenkins(Section):
        project_apps = ListOption()
        jenkins_tasks = TupleOption(
            default=(
                'django_jenkins.tasks.run_pylint',
                'django_jenkins.tasks.with_coverage',
                'django_jenkins.tasks.django_tests',
            ))
        jenkins_test_runner = StringOption()

