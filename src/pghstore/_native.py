from __future__ import print_function
import re

import six

import io


def dumps(obj, key_map=None, value_map=None, encoding="utf-8", return_unicode=False):
    r"""Converts a mapping object as PostgreSQL ``hstore`` format.

    .. sourcecode:: pycon

       >>> dumps({u'a': u'1 "quotes"'}) == b'"a"=>"1 \\"quotes\\""'
       True
       >>> dumps([('key', 'value'), ('k', 'v')]) == b'"key"=>"value","k"=>"v"'
       True

    It accepts only strings as keys and values except ``None`` for values.
    Otherwise it will raise :exc:`TypeError`:

    .. sourcecode:: pycon

       >>> dumps({'null': None}) == b'"null"=>NULL'
       True
       >>> dumps([('a', 1), ('b', 2)])
       Traceback (most recent call last):
         ...
       TypeError: value 1 of key 'a' is not a string

    Or you can pass ``key_map`` and ``value_map`` parameters to workaround
    this:

    .. sourcecode:: pycon

       >>> dumps([('a', 1), ('b', 2)], value_map=str) == b'"a"=>"1","b"=>"2"'
       True

    By applying these options, you can store any other Python objects
    than strings into ``hstore`` values:

    .. sourcecode:: pycon

       >>> import json
       >>> dumps([('a', list(range(3))), ('b', 2)], value_map=json.dumps) == b'"a"=>"[0, 1, 2]","b"=>"2"'
       True
       >>> import pickle
       >>> result = dumps([('a', list(range(3))), ('b', 2)],
       ...       value_map=pickle.dumps)  # doctest: +ELLIPSIS

       ...'"a"=>"...","b"=>"..."'

    It returns a UTF-8 encoded string, but you can change the ``encoding``:

    .. sourcecode:: pycon

       >>> dumps({u'surname': u'\ud64d'}) == b'"surname"=>"\xed\x99\x8d"'
       True
       >>> dumps({u'surname': u'\ud64d'}, encoding='utf-32') == b'"\xff\xfe\x00\x00s\x00\x00\x00u\x00\x00\x00r\x00\x00\x00n\x00\x00\x00a\x00\x00\x00m\x00\x00\x00e\x00\x00\x00"=>"\xff\xfe\x00\x00M\xd6\x00\x00"'
       True

    If you set ``return_unicode`` to ``True``, it will return :class:`six.text_type`
    instead of :class:`str` (byte string):

    .. sourcecode:: pycon

       >>> dumps({'surname': u'\ud64d'}, return_unicode=True) == u'"surname"=>"\ud64d"'
       True

    :param obj: a mapping object to dump
    :param key_map: an optional mapping function that takes a non-string key
                    and returns a mapped string key
    :param value_map: an optional mapping function that takes a non-string
                      value and returns a mapped string value
    :param encoding: a string encode to use
    :param return_unicode: returns an :class:`six.text_type` string instead
                           byte :class:`str`.  ``False`` by default
    :type return_unicode: :class:`bool`
    :returns: a ``hstore`` data
    :rtype: :class:`six.string_types`

    """
    b = io.BytesIO()
    dump(obj, b, key_map=key_map, value_map=value_map, encoding=encoding)
    result = b.getvalue()
    if return_unicode:
        return result.decode(encoding)
    return result


def loads(string, encoding="utf-8", return_type=dict):
    """Parses the passed hstore format ``string`` to a Python mapping object.

    .. sourcecode:: pycon

       >>> loads('"a"=>"1"') == {u'a': u'1'}
       True

    If you want to load a hstore value as any other type than :class:`dict`
    set ``return_type`` parameter.  Note that the constructor has to take
    an iterable object.

    .. sourcecode:: pycon

       >>> loads('"a"=>"1", "b"=>"2"', return_type=list) == [(u'a', u'1'), (u'b', u'2')]
       True
       >>> loads('"return_type"=>"tuple"', return_type=tuple) == ((u'return_type', u'tuple'),)
       True

    :param string: a hstore format string
    :type string: :class:`six.string_types`
    :param encoding: an encoding of the passed ``string``.  if the ``string``
                     is an :class:`six.text_type` string, this parameter will be
                     ignored
    :param return_type: a map type of return value.  default is :class:`dict`
    :returns: a parsed map.  its type is decided by ``return_type`` parameter

    """
    return return_type(parse(string, encoding=encoding))


def dump(obj, file, key_map=None, value_map=None, encoding="utf-8"):
    """Similar to :func:`dumps()` except it writes the result into the passed
    ``file`` object instead of returning it.

    .. sourcecode:: pycon

       >>> import io
       >>> f = io.BytesIO()
       >>> dump({u'a': u'1'}, f)
       >>> f.getvalue() == b'"a"=>"1"'
       True

    :param obj: a mapping object to dump
    :param file: a file object to write into
    :param key_map: an optional mapping function that takes a non-string key
                    and returns a mapped string key
    :param value_map: an optional mapping function that takes a non-string
                      value and returns a mapped string value
    :param encoding: a string encode to use

    """
    if callable(getattr(obj, "items", None)):
        items = obj.items()
    elif callable(getattr(obj, "__iter__", None)):
        items = iter(obj)
    else:
        raise TypeError("expected a mapping object, not " + type(obj).__name__)
    if key_map is None:

        def key_map(key):
            raise TypeError("key %r is not a string" % key)

    elif not callable(key_map):
        raise TypeError("key_map must be callable")
    elif not (value_map is None or callable(value_map)):
        raise TypeError("value_map must be callable")
    write = getattr(file, "write", None)
    if not callable(write):
        raise TypeError(
            "file must be a wrtiable file object that implements " "write() method"
        )
    first = True
    for key, value in items:
        if not isinstance(key, six.string_types) and not isinstance(
            key, six.binary_type
        ):
            key = key_map(key)
        if not isinstance(key, six.binary_type):
            key = key.encode(encoding)
        if value is None:
            value = None
        elif not (
            isinstance(value, six.string_types) or isinstance(value, six.binary_type)
        ):
            if value_map is None:
                raise TypeError("value %r of key %r is not a string" % (value, key))
            value = value_map(value)
        if value is not None and not isinstance(value, six.binary_type):
            value = value.encode(encoding)
        if first:
            write(b'"')
            first = False
        else:
            write(b',"')
        write(escape(key))
        if value is None:
            write(b'"=>NULL')
        else:
            write(b'"=>"')
            write(escape(value))
            write(b'"')


def load(file, encoding="utf-8"):
    """Similar to :func:`loads()` except it reads the passed ``file`` object
    instead of a string.

    """
    read = getattr(file, "read", None)
    if not callable(read):
        raise TypeError(
            "file must be a readable file object that implements " "read() method"
        )
    return loads(read(), encoding=encoding)


#: The pattern of pairs.  It captures following four groups:
#:
#: ``kq``
#:    Quoted key string.
#:
#: ``kb``
#:    Bare key string.
#:
#: ``vq``
#:    Quoted value string.
#:
#: ``vn``
#:    NULL value.
#:
#: ``vb``
#:    Bare value string.
PAIR_RE = re.compile(
    r'\s*(?:"(?P<kq>(?:[^\\"]|\\.)*)")\s*=>\s*'
    r'(?:"(?P<vq>(?:[^\\"]|\\.)*)"|(?P<vn>NULL))'
    r"\s*(?:(?P<ts>,)|$)",
    re.IGNORECASE,
)


def parse(string, encoding="utf-8"):
    r"""More primitive function of :func:`loads()`.  It returns a generator
    that yields pairs of parsed hstore instead of a complete :class:`dict`
    object.

    .. sourcecode:: pycon

       >>> list(parse('"a"=>"1", "b" => "2", "c" => null, "d" => "NULL"')) == [(u'a', u'1'), (u'b', u'2'), (u'c', None), (u'd', u'NULL')]
       True
       >>> list(parse(r'"a=>1"=>"\"b\"=>2"')) == [(u'a=>1', u'"b"=>2')]
       True

    """
    if isinstance(string, six.binary_type):
        string = string.decode(encoding)

    string = string.strip()
    offset = 0
    term_sep = None
    for match in PAIR_RE.finditer(string):
        if match.start() > offset:
            raise ValueError("malformed hstore value: position %d" % offset)

        key = value = None
        kq = match.group("kq")
        if kq:
            key = unescape(kq)

        if key is None:
            raise ValueError("Malformed hstore value starting at position %d" % offset)

        vq = match.group("vq")
        if vq:
            value = unescape(vq)
        elif match.group("vn"):
            value = None
        else:
            raise ValueError("Malformed hstore value starting at position %d" % offset)

        yield key, value

        term_sep = match.group("ts")

        offset = match.end()

    if len(string) > offset or term_sep:
        raise ValueError("malformed hstore value: position %d" % offset)


#: The escape sequence pattern.
ESCAPE_RE = re.compile(r"\\(.)")


def unescape(s):
    r"""Strips escaped sequences.

    .. sourcecode:: pycon

       >>> unescape('abc\\"def\\\\ghi\\ajkl')
       'abc"def\\ghiajkl'
       >>> unescape(r'\"b\"=>2')
       '"b"=>2'

    """
    return ESCAPE_RE.sub(r"\1", s)


def escape(s):
    r"""Escapes quotes and backslashes for use in hstore byte strings.

    .. sourcecode:: pycon

       >>> escape(b'string with "quotes"') == b'string with \\"quotes\\"'
       True
    """
    if isinstance(s, six.binary_type):
        return s.replace(b"\\", b"\\\\").replace(b'"', b'\\"')
    else:
        return s.replace("\\", "\\\\").replace('"', '\\"')
