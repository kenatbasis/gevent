from gevent.hub import PYPY

if PYPY:
    from gevent.corecffi import *
    from gevent.corecffi import __all__, _flags_to_int
else:
    from gevent.corecext import *
    from gevent.corecext import __all__, _flags_to_int
