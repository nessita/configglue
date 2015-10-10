###############################################################################
#
# configglue -- glue for your apps' configuration
#
# A library for simple, DRY configuration of applications
#
# (C) 2009--2011 by Canonical Ltd.
# by John R. Lenton <john.lenton@canonical.com>
# and Ricardo Kirkner <ricardo.kirkner@canonical.com>
#
# Released under the BSD License (see the file LICENSE)
#
# For bug reports, support, and new releases: http://launchpad.net/configglue
#
###############################################################################


from setuptools import (
    find_packages,
    setup,
)

import configglue


install_requires = ['pyxdg']


setup(name='configglue',
      version=configglue.__version__,
      description="Glue to stick OptionParser and ConfigParser together",
      long_description="""
configglue is a library that glues together python's optparse.OptionParser and
ConfigParser.ConfigParser, so that you don't have to repeat yourself when you
want to export the same options to a configuration file and a commandline
interface.
""",
      classifiers=[
        'License :: OSI Approved :: BSD License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        ],
      author='John R. Lenton, Ricardo Kirkner',
      author_email='john.lenton@canonical.com, ricardo.kirkner@canonical.com',
      url='https://launchpad.net/configglue',
      license='BSD License',
      install_requires=install_requires,
      dependency_links=['http://www.freedesktop.org/wiki/Software/pyxdg'],
      packages=find_packages(),
      include_package_data=True,
      zip_safe=True,
      test_suite='configglue.tests',
      tests_require=['mock'],
)
