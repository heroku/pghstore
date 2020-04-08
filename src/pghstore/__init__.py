"""pghstore provides PostgreSQL hstore formatting for Python.

This small module implements a formatter and a loader for hstore_,
one of PostgreSQL_ supplied modules, that stores simple key-value pairs.

.. sourcecode:: pycon

   >>> simple_dictionary = {u'a': u'1'}
   >>> dumps(simple_dictionary) == b'"a"=>"1"'
   True
   >>> loads('"a"=>"1"') == simple_dictionary
   True
   >>> src = [('pgsql', 'mysql'), ('python', 'php'), ('gevent', 'nodejs')]
   >>> loads(dumps(src), return_type=list) == src
   True

You can easily install the package from PyPI_ by using :program:`pip` or
:program:`easy_install`:

.. sourcecode:: console

   $ pip install pghstore

.. _hstore: http://www.postgresql.org/docs/9.1/static/hstore.html
.. _PostgreSQL: http://www.postgresql.org/
.. _PyPI: http://pypi.python.org/pypi/pghstore

"""
from __future__ import absolute_import

from .version import VERSION


try:
    from ._speedups import dumps, loads
except ImportError:
    try:
        from ._native import dump, dumps, load, loads
    except ImportError:
        # XXX required to bootstrap setup.py with no pre-existing six
        pass
else:

    def dump(obj, file):  # noqa: D103
        file.write(dumps(obj, file))

    def load(file):  # noqa: D103
        return loads(file.read())


__all__ = "__version__", "dump", "dumps", "load", "loads"


#: (:class:`six.string_types`) The version string e.g. ``'0.9.2'``.
#:
#: .. deprecated:: 1.0.0
#:    Use :mod:`pghstore.version` module instead.
__version__ = VERSION
