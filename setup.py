###############################################################################
# 
# configglue -- glue for your apps' configuration
# 
# A library for simple, DRY configuration of applications
# 
# (C) 2009--2010 by Canonical Ltd.
# originally by John R. Lenton <john.lenton@canonical.com>
# incorporating schemaconfig as configglue.pyschema
# schemaconfig originally by Ricardo Kirkner <ricardo.kirkner@canonical.com>
# 
# Released under the BSD License (see the file LICENSE)
# 
# For bug reports, support, and new releases: http://launchpad.net/configglue
# 
###############################################################################


from setuptools import setup, find_packages
import sys, os

version = '0.2'

setup(name='configglue',
      version=version,
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
        ],
      author='John R. Lenton',
      author_email='john.lenton@canonical.com',
      url='https://launchpad.net/configglue',
      license='BSD License',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      test_suite='tests',
      )
