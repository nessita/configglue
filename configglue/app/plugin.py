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
from configglue.schema import Schema


__all__ = [
    'Plugin',
    'PluginManager',
]


class Plugin(object):
    schema = Schema
    enabled = False


class PluginManager(object):
    def __init__(self):
        self.available = self.load()

    @property
    def enabled(self):
        return [cls for cls in self.available if cls.enabled]

    def enable(self, plugin):
        plugin.enabled = True

    def disable(self, plugin):
        plugin.enabled = False

    @property
    def schemas(self):
        return [cls.schema for cls in self.enabled]

    def load(self):
        return []

    def register(self, plugin):
        if plugin not in self.available:
            self.available.append(plugin)
