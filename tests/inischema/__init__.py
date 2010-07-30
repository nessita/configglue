# This file is part of configglue, by John R. Lenton <john.lenton@canonical.com>
# (C) 2009 by Canonical Ltd.
# Released under the BSD License (see the file LICENSE)
# For bug reports, support, and new releases: http://launchpad.net/configglue

"""Tests! Who woulda said"""
# Two use cases so far for this file:
#  * make tests a package, so setup.py's "test" command finds the tests
#  * load all the tests

if __name__ == '__main__':
    import unittest

    from configglue.tests import (test_attributed, test_typed,
                                  test_parsers, test_glue)

    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for module in test_attributed, test_typed, test_parsers, test_glue:
        suite.addTest(loader.loadTestsFromModule(module))

    unittest.TextTestRunner(verbosity=2).run(suite)
