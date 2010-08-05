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

"""configglue lives here
"""
from __future__ import absolute_import

from configglue.pyschema import schemaconfigglue, ini2schema

__all__ = ('configglue',)

def configglue(fileobj, *filenames, **kwargs):
    args = kwargs.pop('args', None)
    return schemaconfigglue(ini2schema(fileobj), argv=args)
