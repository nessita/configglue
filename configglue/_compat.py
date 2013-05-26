import sys


PY2 = sys.version_info[0] == 2

if not PY2:
    text_type = str
    string_types = (str,)
    import builtins
    iterkeys = lambda d: iter(d.keys())
    itervalues = lambda d: iter(d.values())
    iteritems = lambda d: iter(d.items())
else:
    text_type = unicode
    string_types = (str, unicode)
    import __builtin__ as builtins
    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()
