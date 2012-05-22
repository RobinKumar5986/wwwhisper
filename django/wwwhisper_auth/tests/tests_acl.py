from django.test import TestCase
from wwwhisper_auth.acl import InvalidPath

import wwwhisper_auth.acl as acl

TEST_USER_EMAIL = 'foo@bar.com'
TEST_LOCATION = '/pub/kika'

class UsersCollectionTest(TestCase):
    def setUp(self):
        self.users_collection = acl.UsersCollection()

    def test_create_user(self):
        user = self.users_collection.create_item(TEST_USER_EMAIL)
        self.assertTrue(TEST_USER_EMAIL, user.email)

    def test_get_user(self):
        user1 = self.users_collection.create_item(TEST_USER_EMAIL)
        user2 = self.users_collection.get(user1.uuid)
        self.assertIsNotNone(user2)
        self.assertEqual(user1.email, user2.email)
        self.assertEqual(user1.uuid, user2.uuid)

    def test_delete_user(self):
        user = self.users_collection.create_item(TEST_USER_EMAIL)
        self.assertIsNotNone(self.users_collection.get(user.uuid))
        self.assertTrue(self.users_collection.delete(user.uuid))
        self.assertIsNone(self.users_collection.get(user.uuid))

    def test_create_user_twice(self):
        self.users_collection.create_item(TEST_USER_EMAIL)
        self.assertRaisesRegexp(acl.CreationException,
                                'User already exists',
                                self.users_collection.create_item,
                                TEST_USER_EMAIL)

    def test_delete_user_twice(self):
        user = self.users_collection.create_item(TEST_USER_EMAIL)
        self.assertTrue(self.users_collection.delete(user.uuid))
        self.assertFalse(self.users_collection.delete(user.uuid))

    def test_get_all_users(self):
        user1 = self.users_collection.create_item('foo@example.com')
        user2 = self.users_collection.create_item('bar@example.com')
        self.assertItemsEqual(['foo@example.com', 'bar@example.com'],
                              [u.email for u in self.users_collection.all()])
        self.users_collection.delete(user1.uuid)
        self.assertItemsEqual(['bar@example.com'],
                              [u.email for u in self.users_collection.all()])

    def test_get_all_users_when_empty(self):
        self.assertListEqual([], list(self.users_collection.all()))

class LocationsCollectionTest(TestCase):
    def setUp(self):
        self.locations_collection = acl.LocationsCollection()

    def test_create_location(self):
        location = self.locations_collection.create_item(TEST_LOCATION)
        self.assertTrue(TEST_LOCATION, location.path)

    def test_get_location(self):
        location1 = self.locations_collection.create_item(TEST_LOCATION)
        location2 = self.locations_collection.get(location1.uuid)
        self.assertIsNotNone(location2)
        self.assertEqual(location1.path, location2.path)
        self.assertEqual(location1.uuid, location2.uuid)

    def test_delete_location(self):
        location = self.locations_collection.create_item(TEST_LOCATION)
        self.assertIsNotNone(self.locations_collection.get(location.uuid))
        self.assertTrue(self.locations_collection.delete(location.uuid))
        self.assertIsNone(self.locations_collection.get(location.uuid))

    def test_create_location_twice(self):
        self.locations_collection.create_item(TEST_LOCATION)
        self.assertRaisesRegexp(acl.CreationException,
                                'Location already exists',
                                self.locations_collection.create_item,
                                TEST_LOCATION)

    def test_delete_location_twice(self):
        location = self.locations_collection.create_item(TEST_LOCATION)
        self.assertTrue(self.locations_collection.delete(location.uuid))
        self.assertFalse(self.locations_collection.delete(location.uuid))

    def test_get_all_locations(self):
        location1 = self.locations_collection.create_item('/foo')
        location2 = self.locations_collection.create_item('/foo/bar')
        self.assertItemsEqual(['/foo/bar', '/foo'],
                              [l.path for l
                               in self.locations_collection.all()])
        self.locations_collection.delete(location1.uuid)
        self.assertItemsEqual(['/foo/bar'],
                              [l.path for l
                               in self.locations_collection.all()])

    def test_get_all_locations_when_empty(self):
        self.assertListEqual([], list(self.locations_collection.all()))

class AclTest(TestCase):

    def test_get_locations(self):
        acl.add_location('/foo/bar')
        acl.add_location('/baz/bar')
        self.assertListEqual(['/baz/bar', '/foo/bar'], sorted(acl.locations()))
        acl.del_location('/foo/bar')
        self.assertListEqual(['/baz/bar'], acl.locations())

    def test_get_locations_when_empty(self):
        self.assertEqual([], acl.locations())


    def test_is_email_valid(self):
        """Test strings taken from BrowserId tests."""
        self.assertTrue(acl.is_email_valid('x@y.z'))
        self.assertTrue(acl.is_email_valid('x@y.z.w'))
        self.assertTrue(acl.is_email_valid('x.v@y.z.w'))
        self.assertTrue(acl.is_email_valid('x_v@y.z.w'))

        self.assertFalse(acl.is_email_valid('x'))
        self.assertFalse(acl.is_email_valid('x@y'))
        self.assertFalse(acl.is_email_valid('@y.z'))
        self.assertFalse(acl.is_email_valid('z@y.z@y.z'))
        self.assertFalse(acl.is_email_valid(''))


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

