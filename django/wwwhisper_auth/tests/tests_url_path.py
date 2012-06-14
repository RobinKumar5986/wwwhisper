from django.test import TestCase
from wwwhisper_auth.url_path import contains_fragment
from wwwhisper_auth.url_path import contains_params
from wwwhisper_auth.url_path import contains_query
from wwwhisper_auth.url_path import decode
from wwwhisper_auth.url_path import is_canonical
from wwwhisper_auth.url_path import strip_query

class UrlPathTest(TestCase):
    def test_is_canonical(self):
        self.assertTrue(is_canonical('/'))
        self.assertTrue(is_canonical('/foo/bar'))
        self.assertTrue(is_canonical('/foo/bar/'))
        self.assertTrue(is_canonical('/foo/bar/  '))


        self.assertFalse(is_canonical(''))
        self.assertFalse(is_canonical('foo'))
        self.assertFalse(is_canonical('//'))
        self.assertFalse(is_canonical(' /'))
        self.assertFalse(is_canonical(' //'))
        self.assertFalse(is_canonical('//foo'))
        self.assertFalse(is_canonical('/foo/bar/..'))
        self.assertFalse(is_canonical('/foo//bar'))
        self.assertFalse(is_canonical('/foo/bar//'))
        self.assertFalse(is_canonical('/foo/bar/./foo'))

    def test_decode(self):
        self.assertEqual('/foo bar#', decode('/foo%20bar%23'))
        self.assertEqual('/FoO', decode('%2F%46%6f%4F'))
        self.assertEqual('/', decode('/'))
        self.assertEqual('/foo', decode('/foo'))
        self.assertEqual('/foo/', decode('/foo/'))

    def test_strip_query(self):
        self.assertEqual('/foo/', strip_query('/foo/?bar=abc'))
        self.assertEqual('/foo', strip_query('/foo?'))
        self.assertEqual('/foo', strip_query('/foo?bar=abc?baz=xyz'))

    def test_contains_fragment(self):
        self.assertTrue(contains_fragment('/foo#123'))
        self.assertTrue(contains_fragment('/foo#'))
        # Encoded fragment separator is OK (it is not treated as
        # fragment separator).
        self.assertFalse(contains_fragment('/foo%23'))

    def test_contains_query(self):
        self.assertTrue(contains_query('/foo?'))
        self.assertFalse(contains_query('/foo'))

    def test_contains_fragment(self):
        self.assertTrue(contains_params('/foo;'))
        self.assertFalse(contains_params('/foo'))
