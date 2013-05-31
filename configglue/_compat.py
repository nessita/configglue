import sys


PY2 = sys.version_info[0] == 2

if not PY2:
    text_type = str
    string_types = (str,)
    import builtins
    iteritems = lambda d: iter(d.items())
else:
    text_type = unicode
    string_types = (str, unicode)
    import __builtin__ as builtins
    iteritems = lambda d: d.iteritems()
