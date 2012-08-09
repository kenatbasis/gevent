# Wrapper module for stdlib os. Written by Geert Jansen.

"""
This module provides cooperative versions of os.read() and os.write().
On Posix platforms this uses non-blocking IO, on Windows a threadpool
is used.
"""

from __future__ import absolute_import

import os
import sys
from gevent.hub import get_hub, reinit
from gevent.socket import EBADF, EAGAIN

try:
    import fcntl
except ImportError:
    fcntl = None

__implements__ = ['read', 'write', 'fork']
__all__ = __implements__

os_read = os.read
os_write = os.write
os_fork = os.fork


def _map_errors(func, *args):
    """Map IOError to OSError."""
    try:
        return func(*args)
    except IOError, e:
        # IOError is structered like OSError in that it has two args: an error
        # number and a error string. So we can just re-raise OSError passing it
        # the IOError args. If at some point we want to catch other errors and
        # map those to OSError as well, we need to make sure that it follows
        # the OSError convention and it gets passed a valid error number and
        # error string.
        raise OSError(*e.args), None, sys.exc_info()[2]


def posix_read(fd, n):
    """Read up to `n` bytes from file descriptor `fd`. Return a string
    containing the bytes read. If end-of-file is reached, an empty string
    is returned."""
    while True:
        flags = _map_errors(fcntl.fcntl, fd, fcntl.F_GETFL, 0)
        if not flags & os.O_NONBLOCK:
            _map_errors(fcntl.fcntl, fd, fcntl.F_SETFL, flags|os.O_NONBLOCK)
        try:
            return os_read(fd, n)
        except OSError, e:
            if e.errno != EAGAIN:
                raise
            sys.exc_clear()
        finally:
            # Be sure to restore the fcntl flags before we switch into the hub.
            # Sometimes multiple file descriptors share the same fcntl flags
            # (e.g. when using ttys/ptys). Those other file descriptors are
            # impacted by our change of flags, so we should restore them
            # before any other code can possibly run.
            if not flags & os.O_NONBLOCK:
                _map_errors(fcntl.fcntl, fd, fcntl.F_SETFL, flags)
        hub = get_hub()
        event = hub.loop.io(fd, 1)
        _map_errors(hub.wait, event)

def posix_write(fd, buf):
    """Write bytes from buffer `buf` to file descriptor `fd`. Return the
    number of bytes written."""
    while True:
        flags = _map_errors(fcntl.fcntl, fd, fcntl.F_GETFL, 0)
        if not flags & os.O_NONBLOCK:
            _map_errors(fcntl.fcntl, fd, fcntl.F_SETFL, flags|os.O_NONBLOCK)
        try:
            return os_write(fd, buf)
        except OSError, e:
            if e.errno != EAGAIN:
                raise
            sys.exc_clear()
        finally:
            # See note in posix_read().
            if not flags & os.O_NONBLOCK:
                _map_errors(fcntl.fcntl, fd, fcntl.F_SETFL, flags)
        hub = get_hub()
        event = hub.loop.io(fd, 2)
        _map_errors(hub.wait, event)


def threadpool_read(fd, n):
    """Read up to `n` bytes from file descriptor `fd`. Return a string
    containing the bytes read. If end-of-file is reached, an empty string
    is returned."""
    threadpool = get_hub().threadpool
    return _map_errors(threadpool.apply, os_read, (fd, n))

def threadpool_write(fd, buf):
    """Write bytes from buffer `buf` to file descriptor `fd`. Return the
    number of bytes written."""
    threadpool = get_hub().threadpool
    return _map_errors(threadpool.apply, os_write, (fd, buf))


if fcntl is None:
    read = threadpool_read
    write = threadpool_write
else:
    read = posix_read
    write = posix_write


if hasattr(os, 'fork'):

    def fork():
        result = os_fork()
        if not result:
            _map_errors(reinit)
        return result

else:
    __all__.remove('fork')
