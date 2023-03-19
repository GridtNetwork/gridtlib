"""Context without std error output."""
import contextlib
import sys


@contextlib.contextmanager
def nostderr():
    """Remove stderr within context."""
    savestderr = sys.stderr

    class Devnull(object):
        def write(self, _):
            pass

        def flush(self):
            pass

    sys.stderr = Devnull()
    try:
        yield
    finally:
        sys.stderr = savestderr
