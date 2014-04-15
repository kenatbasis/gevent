from gevent.hub import PYPY

if PYPY:
    from gevent.corecffi import *
    from gevent import corecffi as _core
else:
    from gevent.corecext import *
    from gevent import corecext as _core

__all__ = _core.__all__
_flags_to_int = _core._flags_to_int
