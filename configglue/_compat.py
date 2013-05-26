import sys


PY2 = sys.version_info[0] == 2

if not PY2:
    text_type = str
    import builtins
else:
    text_type = unicode
    import __builtin__ as builtins
