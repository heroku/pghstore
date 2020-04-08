# -*- coding: utf-8 -*-
import unittest

import pytest
import six

from pghstore import _native

try:
    from pghstore import _speedups
except ImportError:
    _speedups = None


class DumpsTests(unittest.TestCase):
    pghstore = _native

    def assertDumpsMatchesDict(self, s, d):  # noqa: N802
        pairs = [
            '"%s"=>%s'
            % (key, ('"%s"' % value if value is not None else "NULL"))
            for key, value in six.iteritems(d)
        ]
        for pair in pairs:
            self.assertTrue(pair in s)
        self.assertEqual(len(",".join(pairs)), len(s))

    def test_empty(self):
        self.assertEqual(self.pghstore.dumps({}), b"")

    def test_one(self):
        d = {"key": "value"}
        self.assertDumpsMatchesDict(
            self.pghstore.dumps(d, return_unicode=True), d
        )
        d = {"name": "Norge/Noreg"}
        self.assertDumpsMatchesDict(
            self.pghstore.dumps(d, return_unicode=True), d
        )

    def test_two(self):
        d = {"key": "value", "key2": "value2"}
        self.assertDumpsMatchesDict(
            self.pghstore.dumps(d, return_unicode=True), d
        )

    def test_null(self):
        d = {"key": "value", "key2": "value2", "key3": None}
        self.assertDumpsMatchesDict(
            self.pghstore.dumps(d, return_unicode=True), d
        )

    def test_values_with_quotes(self):
        d = {'key_"quoted"_string': 'value_"quoted"_string'}
        self.assertEqual(
            '"key_\\"quoted\\"_string"=>"value_\\"quoted\\"_string"',
            self.pghstore.dumps(d, return_unicode=True),
        )

    def test_escaped_values(self):
        d = {"key_\\escaped\\_string": "value_\\escaped\\_string"}
        self.assertEqual(
            '"key_\\\\escaped\\\\_string"=>"value_\\\\escaped\\\\_string"',
            self.pghstore.dumps(d, return_unicode=True),
        )

    def test_all_the_escapes(self):
        d = {"failing": r"some test \""}
        self.assertEqual(
            b'"failing"=>"some test \\\\\\""', self.pghstore.dumps(d)
        )

    def test_utf8(self):
        d = {
            "key": "value",
            "key2": "value2",
            "key3": None,
            "name": "Noorwe\xc3\xab",
            "name2": "öäå",
        }
        self.assertDumpsMatchesDict(
            self.pghstore.dumps(d, return_unicode=True), d
        )

    def test_large(self):
        d = {
            "name": "Norge/Noreg",
            "name:af": "Noorwe\xeb",
            "name:ar": "\u0627\u0644\u0646\u0631\u0648\u064a\u062c",
            "name:be": "\u041d\u0430\u0440\u0432\u0435\u0433\u0456\u044f",
            "name:br": "Norvegia",
            "name:ca": "Noruega",
            "name:cs": "Norsko",
            "name:cy": "Norwy",
            "name:da": "Norge",
            "name:de": "Norwegen",
            "name:el": "\u039d\u03bf\u03c1\u03b2\u03b7\u03b3\u03af\u03b1",
            "name:en": "Norway",
            "name:eo": "Norvegio",
            "name:es": "Noruega",
            "name:et": "Norra",
            "name:fa": "\u0646\u0631\u0648\u0698",
            "name:fi": "Norja",
            "name:fo": "Noregur",
            "name:fr": "Norv\xe8ge",
            "name:fy": "Noarwegen",
            "name:ga": "An Iorua",
            "name:gd": "Nirribhidh",
            "name:haw": "Nolewai",
            "name:he": "\u05e0\u05d5\u05e8\u05d5\u05d5\u05d2\u05d9\u05d4",
            "name:hr": "Norve\u0161ka",
            "name:hu": "Norv\xe9gia",
            "name:hy": "\u0546\u0578\u0580\u057e\u0565\u0563\u056b\u0561",
            "name:id": "Norwegia",
            "name:is": "Noregur",
            "name:it": "Norvegia",
            "name:ja": "\u30ce\u30eb\u30a6\u30a7\u30fc",
            "name:la": "Norvegia",
            "name:lb": "Norwegen",
            "name:li": "Noorwege",
            "name:lt": "Norvegija",
            "name:lv": "Norv\u0113\u0123ija",
            "name:mn": "\u041d\u043e\u0440\u0432\u0435\u0433\u0438",
            "name:nb": "Norge",
            "name:nl": "Noorwegen",
            "name:nn": "Noreg",
            "name:no": "Norge",
            "name:pl": "Norwegia",
            "name:ru": "\u041d\u043e\u0440\u0432\u0435\u0433\u0438\u044f",
            "name:sk": "N\xf3rsko",
            "name:sl": "Norve\u0161ka",
            "name:sv": "Norge",
            "name:th": "\u0e1b\u0e23\u0e30\u0e40\u0e17\u0e28\u0e19\u0e2d\u0e23\u0e4c\u0e40\u0e27\u0e22\u0e4c",  # noqa: E501
            "name:tr": "Norve\xe7",
            "name:uk": "\u041d\u043e\u0440\u0432\u0435\u0433\u0456\u044f",
            "name:vi": "Na Uy",
            "name:zh": "\u632a\u5a01",
            "name:zh_py": "Nuowei",
            "name:zh_pyt": "Nu\xf3w\u0113i",
            "official_name": "Kongeriket Norge",
            "official_name:be": "\u041a\u0430\u0440\u0430\u043b\u0435\u045e\u0441\u0442\u0432\u0430 \u041d\u0430\u0440\u0432\u0435\u0433\u0456\u044f",  # noqa: E501
            "official_name:el": "\u0392\u03b1\u03c3\u03af\u03bb\u03b5\u03b9\u03bf \u03c4\u03b7\u03c2 \u039d\u03bf\u03c1\u03b2\u03b7\u03b3\u03af\u03b1\u03c2",  # noqa: E501
            "official_name:en": "Kingdom of Norway",
            "official_name:id": "Kerajaan Norwegia",
            "official_name:it": "Regno di Norvegia",
            "official_name:ja": "\u30ce\u30eb\u30a6\u30a7\u30fc\u738b\u56fd",
            "official_name:lb": "Kinneksr\xe4ich Norwegen",
            "official_name:lt": "Norvegijos Karalyst\u0117",
            "official_name:sk": "N\xf3rske kr\xe1\u013eovstvo",
            "official_name:sv": "Konungariket Norge",
            "official_name:vi": "V\u01b0\u01a1ng qu\u1ed1c Na Uy",
        }
        self.assertDumpsMatchesDict(
            self.pghstore.dumps(d, return_unicode=True), d
        )


@pytest.mark.skipif(
    _speedups is None, reason="Could not compile C extensions for tests"
)
class DumpsSpeedupsTests(DumpsTests):
    pghstore = _speedups
