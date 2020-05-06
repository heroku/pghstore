pghstore
========

.. image:: https://secure.travis-ci.org/heroku/pghstore.png?branch=master
   :alt: Build Status
   :target: http://travis-ci.org/heroku/pghstore

This small module implements a formatter and a loader for hstore_,
one of PostgreSQL_ supplied modules, that stores simple key-value pairs.
::

    >>> dumps({u'a': u'1'})
    '"a"=>"1"'
    >>> loads('"a"=>"1"')
    {u'a': u'1'}
    >>> src = [('pgsql', 'mysql'), ('python', 'php'), ('gevent', 'nodejs')]
    >>> loads(dumps(src), return_type=list)
    [(u'pgsql', u'mysql'), (u'python', u'php'), (u'gevent', u'nodejs')]

You can easily install the package from PyPI_ by using ``pip`` or
``easy_install``::

    $ pip install pghstore

Visit the website to read its documentation:

https://pghstore.readthedocs.io/

.. _hstore: http://www.postgresql.org/docs/9.1/static/hstore.html
.. _PostgreSQL: http://www.postgresql.org/
.. _PyPI: http://pypi.python.org/pypi/pghstore


Changelog
---------

Version 2.0.2
'''''''''''''

- Fixes a segmentation fault caused by trying to parse invalid HStore strings.
  See also (`#13`_)

.. _#13: https://github.com/heroku/pghstore/issues/13

Version 2.0.1 (unreleased to PyPI)
''''''''''''''''''''''''''''''''''

- Fixes a regression in behaviour with escape characters

Version 2.0.0 (unreleased to PyPI)
''''''''''''''''''''''''''''''''''

- Supports Python 2.7+ and Python3.5+ both natively and with C extension

- Drops support for Python 2.5 and 2.6

Version 0.9.2
'''''''''''''

Released on May 3, 2012.

- Fixed escaping of quotes and backslshes. Patched by Dan Watson (`#2`_).

.. _#2: https://github.com/StyleShare/pghstore/pull/2


Version 0.9.1
'''''''''''''

Released on January 2, 2012.

- Now it is aware of ``NULL`` values.  ``NULL`` values become ``None`` in
  Python and vice versa.

Version 0.9.0
'''''''''''''

Released on December 22, 2011.

- Initial version.
