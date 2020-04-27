# -*- coding: utf-8 -*-
import unittest
import pytest

from pghstore import _native

try:
    from pghstore import _speedups
except ImportError:
    _speedups = None


class LoadsTests(unittest.TestCase):
    pghstore = _native

    def test_empty(self):
        self.assertEqual(self.pghstore.loads(""), {})

    def test_simple(self):
        self.assertEqual(self.pghstore.loads('"key" => "value"'), {"key": "value"})

        self.assertEqual(
            self.pghstore.loads('"key" => "value", "key2" => "value2"'),
            {"key": "value", "key2": "value2"},
        )

    def test_escaped_double_quote(self):
        self.assertEqual(
            self.pghstore.loads(r'"k\"ey" => "va\"lue"'), {'k"ey': 'va"lue'}
        )

    def test_null(self):
        self.assertEqual(self.pghstore.loads('"key" => null'), {"key": None})
        self.assertEqual(self.pghstore.loads('"key" => NULL'), {"key": None})
        self.assertEqual(
            self.pghstore.loads('"key" => NULL, "key2" => "value2"'),
            {"key": None, "key2": "value2"},
        )
        self.assertEqual(
            self.pghstore.loads(
                b'"key0" => "value0", "key" => NULL, "key2" => "value2"'
            ),
            {"key0": "value0", "key": None, "key2": "value2"},
        )

    def test_utf8(self):
        self.maxDiff = None
        # self.assertEqual(self.pghstore.loads('"åäö" => "åäö"'), {"åäö": "åäö"})
        s = u'"name"=>"Noorwe\xeb", "name2"=>"öäå"'.encode("utf-8")
        self.assertEqual(
            self.pghstore.loads(s),
            {"name": b"Noorwe\xc3\xab".decode("utf-8"), "name2": u"öäå"},
        )
        names = b'"name"=>"Norge/Noreg", "name:af"=>"Noorwe\xc3\xab", "name:ar"=>"\xd8\xa7\xd9\x84\xd9\x86\xd8\xb1\xd9\x88\xd9\x8a\xd8\xac", "name:be"=>"\xd0\x9d\xd0\xb0\xd1\x80\xd0\xb2\xd0\xb5\xd0\xb3\xd1\x96\xd1\x8f", "name:br"=>"Norvegia", "name:ca"=>"Noruega", "name:cs"=>"Norsko", "name:cy"=>"Norwy", "name:da"=>"Norge", "name:de"=>"Norwegen", "name:el"=>"\xce\x9d\xce\xbf\xcf\x81\xce\xb2\xce\xb7\xce\xb3\xce\xaf\xce\xb1", "name:en"=>"Norway", "name:eo"=>"Norvegio", "name:es"=>"Noruega", "name:et"=>"Norra", "name:fa"=>"\xd9\x86\xd8\xb1\xd9\x88\xda\x98", "name:fi"=>"Norja", "name:fo"=>"Noregur", "name:fr"=>"Norv\xc3\xa8ge", "name:fy"=>"Noarwegen", "name:ga"=>"An Iorua", "name:gd"=>"Nirribhidh", "name:he"=>"\xd7\xa0\xd7\x95\xd7\xa8\xd7\x95\xd7\x95\xd7\x92\xd7\x99\xd7\x94", "name:hr"=>"Norve\xc5\xa1ka", "name:hu"=>"Norv\xc3\xa9gia", "name:hy"=>"\xd5\x86\xd5\xb8\xd6\x80\xd5\xbe\xd5\xa5\xd5\xa3\xd5\xab\xd5\xa1", "name:id"=>"Norwegia", "name:is"=>"Noregur", "name:it"=>"Norvegia", "name:ja"=>"\xe3\x83\x8e\xe3\x83\xab\xe3\x82\xa6\xe3\x82\xa7\xe3\x83\xbc", "name:la"=>"Norvegia", "name:lb"=>"Norwegen", "name:li"=>"Noorwege", "name:lt"=>"Norvegija", "name:lv"=>"Norv\xc4\x93\xc4\xa3ija", "name:mn"=>"\xd0\x9d\xd0\xbe\xd1\x80\xd0\xb2\xd0\xb5\xd0\xb3\xd0\xb8", "name:nb"=>"Norge", "name:nl"=>"Noorwegen", "name:nn"=>"Noreg", "name:no"=>"Norge", "name:pl"=>"Norwegia", "name:ru"=>"\xd0\x9d\xd0\xbe\xd1\x80\xd0\xb2\xd0\xb5\xd0\xb3\xd0\xb8\xd1\x8f", "name:sk"=>"N\xc3\xb3rsko", "name:sl"=>"Norve\xc5\xa1ka", "name:sv"=>"Norge", "name:th"=>"\xe0\xb8\x9b\xe0\xb8\xa3\xe0\xb8\xb0\xe0\xb9\x80\xe0\xb8\x97\xe0\xb8\xa8\xe0\xb8\x99\xe0\xb8\xad\xe0\xb8\xa3\xe0\xb9\x8c\xe0\xb9\x80\xe0\xb8\xa7\xe0\xb8\xa2\xe0\xb9\x8c", "name:tr"=>"Norve\xc3\xa7", "name:uk"=>"\xd0\x9d\xd0\xbe\xd1\x80\xd0\xb2\xd0\xb5\xd0\xb3\xd1\x96\xd1\x8f", "name:vi"=>"Na Uy", "name:zh"=>"\xe6\x8c\xaa\xe5\xa8\x81", "name:haw"=>"Nolewai", "name:zh_py"=>"Nuowei", "name:zh_pyt"=>"Nu\xc3\xb3w\xc4\x93i", "official_name"=>"Kongeriket Norge", "official_name:be"=>"\xd0\x9a\xd0\xb0\xd1\x80\xd0\xb0\xd0\xbb\xd0\xb5\xd1\x9e\xd1\x81\xd1\x82\xd0\xb2\xd0\xb0 \xd0\x9d\xd0\xb0\xd1\x80\xd0\xb2\xd0\xb5\xd0\xb3\xd1\x96\xd1\x8f", "official_name:el"=>"\xce\x92\xce\xb1\xcf\x83\xce\xaf\xce\xbb\xce\xb5\xce\xb9\xce\xbf \xcf\x84\xce\xb7\xcf\x82 \xce\x9d\xce\xbf\xcf\x81\xce\xb2\xce\xb7\xce\xb3\xce\xaf\xce\xb1\xcf\x82", "official_name:en"=>"Kingdom of Norway", "official_name:id"=>"Kerajaan Norwegia", "official_name:it"=>"Regno di Norvegia", "official_name:ja"=>"\xe3\x83\x8e\xe3\x83\xab\xe3\x82\xa6\xe3\x82\xa7\xe3\x83\xbc\xe7\x8e\x8b\xe5\x9b\xbd", "official_name:lb"=>"Kinneksr\xc3\xa4ich Norwegen", "official_name:lt"=>"Norvegijos Karalyst\xc4\x97", "official_name:sk"=>"N\xc3\xb3rske kr\xc3\xa1\xc4\xbeovstvo", "official_name:sv"=>"Konungariket Norge", "official_name:vi"=>"V\xc6\xb0\xc6\xa1ng qu\xe1\xbb\x91c Na Uy"'
        self.assertListEqual(
            self.pghstore.loads(names, return_type=list),
            [
                (u"name", u"Norge/Noreg"),
                (u"name:af", b"Noorwe\xc3\xab".decode("utf-8")),
                (
                    u"name:ar",
                    b"\xd8\xa7\xd9\x84\xd9\x86\xd8\xb1\xd9\x88\xd9\x8a\xd8\xac".decode(
                        "utf-8"
                    ),
                ),
                (
                    u"name:be",
                    b"\xd0\x9d\xd0\xb0\xd1\x80\xd0\xb2\xd0\xb5\xd0\xb3\xd1\x96\xd1\x8f".decode(
                        "utf-8"
                    ),
                ),
                (u"name:br", u"Norvegia"),
                (u"name:ca", u"Noruega"),
                (u"name:cs", u"Norsko"),
                (u"name:cy", u"Norwy"),
                (u"name:da", u"Norge"),
                (u"name:de", u"Norwegen"),
                (
                    u"name:el",
                    b"\xce\x9d\xce\xbf\xcf\x81\xce\xb2\xce\xb7\xce\xb3\xce\xaf\xce\xb1".decode(
                        "utf-8"
                    ),
                ),
                (u"name:en", u"Norway"),
                (u"name:eo", u"Norvegio"),
                (u"name:es", u"Noruega"),
                (u"name:et", u"Norra"),
                (u"name:fa", b"\xd9\x86\xd8\xb1\xd9\x88\xda\x98".decode("utf-8")),
                (u"name:fi", u"Norja"),
                (u"name:fo", u"Noregur"),
                (u"name:fr", b"Norv\xc3\xa8ge".decode("utf-8")),
                (u"name:fy", u"Noarwegen"),
                (u"name:ga", u"An Iorua"),
                (u"name:gd", u"Nirribhidh"),
                (
                    u"name:he",
                    b"\xd7\xa0\xd7\x95\xd7\xa8\xd7\x95\xd7\x95\xd7\x92\xd7\x99\xd7\x94".decode(
                        "utf-8"
                    ),
                ),
                (u"name:hr", b"Norve\xc5\xa1ka".decode("utf-8")),
                (u"name:hu", b"Norv\xc3\xa9gia".decode("utf-8")),
                (
                    u"name:hy",
                    b"\xd5\x86\xd5\xb8\xd6\x80\xd5\xbe\xd5\xa5\xd5\xa3\xd5\xab\xd5\xa1".decode(
                        "utf-8"
                    ),
                ),
                (u"name:id", u"Norwegia"),
                (u"name:is", u"Noregur"),
                (u"name:it", u"Norvegia"),
                (
                    u"name:ja",
                    b"\xe3\x83\x8e\xe3\x83\xab\xe3\x82\xa6\xe3\x82\xa7\xe3\x83\xbc".decode(
                        "utf-8"
                    ),
                ),
                (u"name:la", u"Norvegia"),
                (u"name:lb", u"Norwegen"),
                (u"name:li", u"Noorwege"),
                (u"name:lt", u"Norvegija"),
                (u"name:lv", b"Norv\xc4\x93\xc4\xa3ija".decode("utf-8")),
                (
                    u"name:mn",
                    b"\xd0\x9d\xd0\xbe\xd1\x80\xd0\xb2\xd0\xb5\xd0\xb3\xd0\xb8".decode(
                        "utf-8"
                    ),
                ),
                (u"name:nb", u"Norge"),
                (u"name:nl", u"Noorwegen"),
                (u"name:nn", u"Noreg"),
                (u"name:no", u"Norge"),
                (u"name:pl", u"Norwegia"),
                (
                    u"name:ru",
                    b"\xd0\x9d\xd0\xbe\xd1\x80\xd0\xb2\xd0\xb5\xd0\xb3\xd0\xb8\xd1\x8f".decode(
                        "utf-8"
                    ),
                ),
                (u"name:sk", b"N\xc3\xb3rsko".decode("utf-8")),
                (u"name:sl", b"Norve\xc5\xa1ka".decode("utf-8")),
                (u"name:sv", u"Norge"),
                (
                    u"name:th",
                    b"\xe0\xb8\x9b\xe0\xb8\xa3\xe0\xb8\xb0\xe0\xb9\x80\xe0\xb8\x97\xe0\xb8\xa8\xe0\xb8\x99\xe0\xb8\xad\xe0\xb8\xa3\xe0\xb9\x8c\xe0\xb9\x80\xe0\xb8\xa7\xe0\xb8\xa2\xe0\xb9\x8c".decode(
                        "utf-8"
                    ),
                ),
                (u"name:tr", b"Norve\xc3\xa7".decode("utf-8")),
                (
                    u"name:uk",
                    b"\xd0\x9d\xd0\xbe\xd1\x80\xd0\xb2\xd0\xb5\xd0\xb3\xd1\x96\xd1\x8f".decode(
                        "utf-8"
                    ),
                ),
                (u"name:vi", u"Na Uy"),
                (u"name:zh", b"\xe6\x8c\xaa\xe5\xa8\x81".decode("utf-8")),
                (u"name:haw", u"Nolewai"),
                (u"name:zh_py", u"Nuowei"),
                (u"name:zh_pyt", b"Nu\xc3\xb3w\xc4\x93i".decode("utf-8")),
                (u"official_name", u"Kongeriket Norge"),
                (
                    u"official_name:be",
                    b"\xd0\x9a\xd0\xb0\xd1\x80\xd0\xb0\xd0\xbb\xd0\xb5\xd1\x9e\xd1\x81\xd1\x82\xd0\xb2\xd0\xb0 \xd0\x9d\xd0\xb0\xd1\x80\xd0\xb2\xd0\xb5\xd0\xb3\xd1\x96\xd1\x8f".decode(
                        "utf-8"
                    ),
                ),
                (
                    u"official_name:el",
                    b"\xce\x92\xce\xb1\xcf\x83\xce\xaf\xce\xbb\xce\xb5\xce\xb9\xce\xbf \xcf\x84\xce\xb7\xcf\x82 \xce\x9d\xce\xbf\xcf\x81\xce\xb2\xce\xb7\xce\xb3\xce\xaf\xce\xb1\xcf\x82".decode(
                        "utf-8"
                    ),
                ),
                (u"official_name:en", u"Kingdom of Norway"),
                (u"official_name:id", u"Kerajaan Norwegia"),
                (u"official_name:it", u"Regno di Norvegia"),
                (
                    u"official_name:ja",
                    b"\xe3\x83\x8e\xe3\x83\xab\xe3\x82\xa6\xe3\x82\xa7\xe3\x83\xbc\xe7\x8e\x8b\xe5\x9b\xbd".decode(
                        "utf-8"
                    ),
                ),
                (u"official_name:lb", b"Kinneksr\xc3\xa4ich Norwegen".decode("utf-8")),
                (u"official_name:lt", b"Norvegijos Karalyst\xc4\x97".decode("utf-8")),
                (
                    u"official_name:sk",
                    b"N\xc3\xb3rske kr\xc3\xa1\xc4\xbeovstvo".decode("utf-8"),
                ),
                (u"official_name:sv", u"Konungariket Norge"),
                (
                    u"official_name:vi",
                    b"V\xc6\xb0\xc6\xa1ng qu\xe1\xbb\x91c Na Uy".decode("utf-8"),
                ),
            ],
        )

    def test_decode_failure_key(self):
        s = b'"\x01\xb6\xc3\xa4\xc3\xa5"=>"123"'
        with self.assertRaises(UnicodeDecodeError):
            self.pghstore.loads(s)

    def test_decode_failure_value(self):
        s = b'"key"=>"\x01\xb6\xc3\xa4\xc3\xa5"'
        with self.assertRaises(UnicodeDecodeError):
            self.pghstore.loads(s)

    def test_decode_failure_weird_quote(self):
        s = b'"key"=>NULL"'
        with self.assertRaises(ValueError):
            self.pghstore.loads(s)

    def test_decode_failure_weird_quote2(self):
        s = b'"keyokay"=>NULL, "key"=>NULL"'
        with self.assertRaises(ValueError):
            self.pghstore.loads(s)

    def test_invalid_kv_separator(self):
        s = '"key" => NULL, "key2" : "value2"'
        with self.assertRaises(ValueError):
            self.pghstore.loads(s)

    def test_invalid_trailing_comma(self):
        s = '"key" => NULL, "key2" => "value2",'
        with self.assertRaises(ValueError):
            self.pghstore.loads(s)

    def test_invalid_trailing_comma_with_space(self):
        s = '"key" => NULL, "key2" => "value2",   '
        with self.assertRaises(ValueError):
            self.pghstore.loads(s)

    def test_invalid_trailing_quote(self):
        s = '"key" => NULL, "key2" => "value2" "quoted"'
        with self.assertRaises(ValueError):
            self.pghstore.loads(s)

    def test_invalid_trailing_junk(self):
        s = '"key" => NULL, "key2" => "value2", junk'
        with self.assertRaises(ValueError):
            self.pghstore.loads(s)

    def test_invalid_starting_junk(self):
        s = 'junk, "key" => NULL, "key2" => "value2"'
        with self.assertRaises(ValueError):
            self.pghstore.loads(s)

    def test_round_trip_double_quotes(self):
        d = {'key_"quoted"_string': 'value_"quoted"_string'}
        self.assertDictEqual(d, self.pghstore.loads(self.pghstore.dumps(d)))

    def test_round_trip_escaped_characters(self):
        d = {"key_\\escaped\\_string": "value_\\escaped\\_string"}
        self.assertDictEqual(d, self.pghstore.loads(self.pghstore.dumps(d)))

    def test_load_escape_with_dquote(self):
        s = r'"failing"=>"some test \\\""'
        self.assertDictEqual({"failing": r"some test \""}, self.pghstore.loads(s))

    def test_roundtrip_with_all_the_escapables(self):
        d = {"failing": r"some test \""}
        self.assertDictEqual(d, self.pghstore.loads(self.pghstore.dumps(d)))

    def test_roundtrip_multiple(self):
        src = [("pgsql", "mysql"), ("python", "php"), ("gevent", "nodejs")]
        self.assertEqual(
            src, self.pghstore.loads(self.pghstore.dumps(src), return_type=list)
        )


@pytest.mark.skipif(
    _speedups is None, reason="Could not compile C extensions for tests"
)
class LoadsSpeedupsTests(LoadsTests):
    pghstore = _speedups
