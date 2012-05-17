from django.test import TestCase
from wwwhisper_auth.acl import InvalidPath

import wwwhisper_auth.acl as acl

class Acl(TestCase):
    def test_add_location(self):
        self.assertFalse(acl.find_location('/foo/bar'))
        self.assertTrue(acl.add_location('/foo/bar'))
        self.assertTrue(acl.find_location('/foo/bar'))

    def test_add_location_twice(self):
        self.assertTrue(acl.add_location('/foo/bar'))
        self.assertFalse(acl.add_location('/foo/bar'))

    def test_del_location(self):
        self.assertTrue(acl.add_location('/foo/bar'))
        self.assertTrue(acl.del_location('/foo/bar'))
        self.assertFalse(acl.find_location('/foo/bar'))

    def test_del_missing_location(self):
        self.assertFalse(acl.del_location('/foo/bar'))

    def test_get_locations(self):
        acl.add_location('/foo/bar')
        acl.add_location('/baz/bar')
        self.assertListEqual(['/baz/bar', '/foo/bar'], sorted(acl.locations()))
        acl.del_location('/foo/bar')
        self.assertListEqual(['/baz/bar'], acl.locations())

    def test_get_locations_when_empty(self):
        self.assertEqual([], acl.locations())

    def test_add_user(self):
        self.assertFalse(acl.find_user('foo@example.com'))
        self.assertTrue(acl.add_user('foo@example.com'))
        self.assertTrue(acl.find_user('foo@example.com'))

    def test_add_user_twice(self):
        self.assertTrue(acl.add_user('foo@example.com'))
        self.assertFalse(acl.add_user('foo@example.com'))

    def test_del_user(self):
        self.assertTrue(acl.add_user('foo@example.com'))
        self.assertTrue(acl.del_user('foo@example.com'))
        self.assertFalse(acl.find_user('foo@example.com'))

    def test_del_missing_user(self):
        self.assertFalse(acl.del_user('foo@example.com'))

    def test_get_emails(self):
        acl.add_user('foo@example.com')
        acl.add_user('bar@example.com')
        self.assertListEqual(['bar@example.com', 'foo@example.com'],
                             sorted(acl.emails()))
        acl.del_user('foo@example.com')
        self.assertListEqual(['bar@example.com'], acl.emails())

    def test_get_emails_when_empty(self):
        self.assertEqual([], acl.emails())

    def test_grant_access(self):
        acl.add_user('foo@example.com')
        acl.add_location('/foo/bar')
        self.assertFalse(acl.can_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.grant_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar'))

    def test_grant_access_to_non_existing_location(self):
        acl.add_user('foo@example.com')
        self.assertFalse(acl.find_location('/foo/bar'))
        self.assertRaises(LookupError, acl.grant_access,
                          'foo@example.com', '/foo/bar')

    def test_grant_access_for_non_existing_user(self):
        acl.add_location('/foo/bar')
        self.assertFalse(acl.find_user('foo@example.com'))
        self.assertTrue(acl.grant_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.find_user('foo@example.com'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar'))

    def test_grant_access_if_already_granted(self):
        acl.add_location('/foo/bar')
        self.assertTrue(acl.grant_access('foo@example.com', '/foo/bar'))
        self.assertFalse(acl.grant_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar'))

    def test_grant_access_gives_access_to_sublocations(self):
        acl.add_location('/foo/bar')
        self.assertTrue(acl.grant_access('foo@example.com', '/foo/bar'))

        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar/'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar/b'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar/baz'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar/baz/bar/'))

        self.assertFalse(acl.can_access('foo@example.com', '/foo/ba'))
        self.assertFalse(acl.can_access('foo@example.com', '/foo/barr'))
        self.assertFalse(acl.can_access('foo@example.com', '/foo/foo/bar'))

    def test_more_specific_location_takes_precedence_over_generic(self):
        acl.add_location('/foo/bar')
        self.assertTrue(acl.grant_access('foo@example.com', '/foo/bar'))
        acl.add_location('/foo/bar/baz/')
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar/ba'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar/bazz'))

        self.assertFalse(acl.can_access('foo@example.com', '/foo/bar/baz'))
        self.assertFalse(acl.can_access('foo@example.com', '/foo/bar/baz/'))
        self.assertFalse(acl.can_access('foo@example.com', '/foo/bar/baz/bam'))

    def test_trailing_slash_ignored(self):
        # TODO: what about this / here.
        acl.add_location('/foo/bar/')
        self.assertTrue(acl.grant_access('foo@example.com', '/foo/bar/'))

        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar/'))

        self.assertFalse(acl.can_access('foo@example.com', '/foo/barr'))
        self.assertFalse(acl.can_access('foo@example.com', '/foo/ba/'))

    def test_grant_access_to_root(self):
        acl.add_location('/')
        self.assertTrue(acl.grant_access('foo@example.com', '/'))

        self.assertTrue(acl.can_access('foo@example.com', '/'))
        self.assertTrue(acl.can_access('foo@example.com', '/f'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar/baz'))

    def test_revoke_access(self):
        acl.add_location('/foo/bar')
        self.assertTrue(acl.grant_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.revoke_access('foo@example.com', '/foo/bar'))
        self.assertFalse(acl.can_access('foo@example.com', '/foo/bar'))

    def test_revoke_access_to_non_existing_location(self):
        acl.add_location('/foo/bar')
        self.assertFalse(acl.revoke_access('foo@example.com', '/foo/bar'))

    def test_revoke_non_granted_access(self):
        self.assertRaises(LookupError, acl.revoke_access,
                          'foo@example.com', '/foo/bar')

    def test_get_allowed_emails(self):
        acl.add_location('/foo/bar')
        acl.add_location('/foo/baz')

        acl.grant_access('foo@example.com', '/foo/bar')
        acl.grant_access('baz@example.com', '/foo/baz')
        acl.grant_access('bar@example.com', '/foo/bar')

        self.assertListEqual(['bar@example.com', 'foo@example.com'],
                             sorted(acl.allowed_emails('/foo/bar')))
        self.assertListEqual(['baz@example.com'],
                             acl.allowed_emails('/foo/baz'))

        acl.revoke_access('foo@example.com', '/foo/bar')
        self.assertEqual(['bar@example.com'], acl.allowed_emails('/foo/bar'))

    def test_get_allowed_emails_when_empty(self):
        self.assertEqual([], acl.allowed_emails('/foo/bar'))

    def test_encode_path(self):
        self.assertEqual('/', acl.encode_path('/'))
        self.assertEqual('/foo', acl.encode_path('/foo'))
        self.assertEqual('/foo/', acl.encode_path('/foo/'))
        self.assertEqual('/foo.', acl.encode_path('/foo.'))
        self.assertEqual('/foo..', acl.encode_path('/foo..'))
        self.assertEqual('/foo%20bar', acl.encode_path('/foo bar'))
        self.assertEqual('/foo~', acl.encode_path('/foo~'))
        self.assertEqual('/foo/bar%21%407%2A', acl.encode_path('/foo/bar!@7*'))

    def test_encode_invalid_path(self):
        self.assertRaisesRegexp(InvalidPath, "empty", acl.encode_path,
                                '')
        self.assertRaisesRegexp(InvalidPath, "empty", acl.encode_path,
                                ' ')
        self.assertRaisesRegexp(InvalidPath, "parameters", acl.encode_path,
                                '/foo;bar')
        self.assertRaisesRegexp(InvalidPath, "query", acl.encode_path,
                                '/foo?s=bar')
        self.assertRaisesRegexp(InvalidPath, "fragment", acl.encode_path,
                                '/foo#bar')
        self.assertRaisesRegexp(InvalidPath, "scheme", acl.encode_path,
                                'file://foo')
        self.assertRaisesRegexp(InvalidPath, "domain", acl.encode_path,
                                'http://example.com/foo')
        self.assertRaisesRegexp(InvalidPath, "port", acl.encode_path,
                                'http://example.com:81/foo')
        self.assertRaisesRegexp(InvalidPath, "username", acl.encode_path,
                                'http://boo@example.com/foo')
        self.assertRaisesRegexp(InvalidPath, "normalized", acl.encode_path,
                                '/foo/./')
        self.assertRaisesRegexp(InvalidPath, "normalized", acl.encode_path,
                                '/foo/..')
        self.assertRaisesRegexp(InvalidPath, "normalized", acl.encode_path,
                                '/foo/../bar/')
        self.assertRaisesRegexp(InvalidPath, "normalized", acl.encode_path,
                                '/foo//bar')
    # TODO: test that removing user and location revokes access

