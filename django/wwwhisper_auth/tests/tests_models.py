from django.forms import ValidationError
from django.test import TestCase
from wwwhisper_auth.models import CreationException
from wwwhisper_auth.models import InvalidPath
from wwwhisper_auth.models import can_access
import wwwhisper_auth.models as models

FAKE_UUID = '41be0192-0fcc-4a9c-935d-69243b75533c'
TEST_USER_EMAIL = 'foo@bar.com'
TEST_LOCATION = '/pub/kika'

class CollectionTestCase(TestCase):
    def setUp(self):
        self.locations_collection = models.LocationsCollection()
        self.users_collection = models.UsersCollection()

class UsersCollectionTest(CollectionTestCase):
    def test_create_user(self):
        user = self.users_collection.create_item(TEST_USER_EMAIL)
        self.assertTrue(TEST_USER_EMAIL, user.email)

    def test_get_user(self):
        user1 = self.users_collection.create_item(TEST_USER_EMAIL)
        user2 = self.users_collection.get_item(user1.uuid)
        self.assertIsNotNone(user2)
        self.assertEqual(user1.email, user2.email)
        self.assertEqual(user1.uuid, user2.uuid)

    def test_delete_user(self):
        user = self.users_collection.create_item(TEST_USER_EMAIL)
        self.assertIsNotNone(self.users_collection.get_item(user.uuid))
        self.assertTrue(self.users_collection.delete_item(user.uuid))
        self.assertIsNone(self.users_collection.get_item(user.uuid))

    def test_create_user_twice(self):
        self.users_collection.create_item(TEST_USER_EMAIL)
        self.assertRaisesRegexp(CreationException,
                                'User already exists',
                                self.users_collection.create_item,
                                TEST_USER_EMAIL)

    def test_delete_user_twice(self):
        user = self.users_collection.create_item(TEST_USER_EMAIL)
        self.assertTrue(self.users_collection.delete_item(user.uuid))
        self.assertFalse(self.users_collection.delete_item(user.uuid))

    def test_get_all_users(self):
        user1 = self.users_collection.create_item('foo@example.com')
        user2 = self.users_collection.create_item('bar@example.com')
        self.assertItemsEqual(['foo@example.com', 'bar@example.com'],
                              [u.email for u in self.users_collection.all()])
        self.users_collection.delete_item(user1.uuid)
        self.assertItemsEqual(['bar@example.com'],
                              [u.email for u in self.users_collection.all()])

    def test_get_all_users_when_empty(self):
        self.assertListEqual([], list(self.users_collection.all()))


    def test_email_validation(self):
        """Test strings taken from BrowserId tests."""
        self.assertIsNotNone(self.users_collection.create_item('x@y.z'))
        self.assertIsNotNone(self.users_collection.create_item('x@y.z.w'))
        self.assertIsNotNone(self.users_collection.create_item('x.v@y.z.w'))
        self.assertIsNotNone(self.users_collection.create_item('x_v@y.z.w'))

        self.assertRaisesRegexp(CreationException,
                                'Invalid email format',
                                self.users_collection.create_item,
                                'x')
        self.assertRaisesRegexp(CreationException,
                                'Invalid email format',
                                self.users_collection.create_item,
                                'x@y')
        self.assertRaisesRegexp(CreationException,
                                'Invalid email format',
                                self.users_collection.create_item,
                                '@y.z')
        self.assertRaisesRegexp(CreationException,
                                'Invalid email format',
                                self.users_collection.create_item,
                                'z@y.z@y.z')
        self.assertRaisesRegexp(CreationException,
                                'Invalid email format',
                                self.users_collection.create_item,
                                '')

class LocationsCollectionTest(CollectionTestCase):
    def test_create_location(self):
        location = self.locations_collection.create_item(TEST_LOCATION)
        self.assertTrue(TEST_LOCATION, location.path)

    def test_get_location(self):
        location1 = self.locations_collection.create_item(TEST_LOCATION)
        location2 = self.locations_collection.get_item(location1.uuid)
        self.assertIsNotNone(location2)
        self.assertEqual(location1.path, location2.path)
        self.assertEqual(location1.uuid, location2.uuid)

    def test_delete_location(self):
        location = self.locations_collection.create_item(TEST_LOCATION)
        self.assertIsNotNone(self.locations_collection.get_item(location.uuid))
        self.assertTrue(self.locations_collection.delete_item(location.uuid))
        self.assertIsNone(self.locations_collection.get_item(location.uuid))

    def test_create_location_twice(self):
        self.locations_collection.create_item(TEST_LOCATION)
        self.assertRaisesRegexp(CreationException,
                                'Location already exists',
                                self.locations_collection.create_item,
                                TEST_LOCATION)

    def test_delete_location_twice(self):
        location = self.locations_collection.create_item(TEST_LOCATION)
        self.assertTrue(self.locations_collection.delete_item(location.uuid))
        self.assertFalse(self.locations_collection.delete_item(location.uuid))

    def test_get_all_locations(self):
        location1 = self.locations_collection.create_item('/foo')
        location2 = self.locations_collection.create_item('/foo/bar')
        self.assertItemsEqual(['/foo/bar', '/foo'],
                              [l.path for l
                               in self.locations_collection.all()])
        self.locations_collection.delete_item(location1.uuid)
        self.assertItemsEqual(['/foo/bar'],
                              [l.path for l
                               in self.locations_collection.all()])

    def test_get_all_locations_when_empty(self):
        self.assertListEqual([], list(self.locations_collection.all()))

    def test_grant_access(self):
        user = self.users_collection.create_item(TEST_USER_EMAIL)
        location = self.locations_collection.create_item(TEST_LOCATION)
        self.assertFalse(can_access(TEST_USER_EMAIL, TEST_LOCATION))
        (perm, created) = location.grant_access(user.uuid)
        self.assertTrue(created)
        self.assertIsNotNone(perm)
        self.assertTrue(can_access(TEST_USER_EMAIL, TEST_LOCATION))

    def test_grant_access_for_not_existing_user(self):
        location = self.locations_collection.create_item(TEST_LOCATION)
        self.assertRaisesRegexp(LookupError,
                                'User not found',
                                location.grant_access,
                                FAKE_UUID)

    def test_grant_access_if_already_granted(self):
        location = self.locations_collection.create_item(TEST_LOCATION)
        user = self.users_collection.create_item(TEST_USER_EMAIL)
        (permission1, created1) = location.grant_access(user.uuid)
        self.assertTrue(created1)
        (permission2, created2) = location.grant_access(user.uuid)
        self.assertFalse(created2)
        self.assertEqual(permission1, permission2)
        self.assertEqual(TEST_USER_EMAIL, permission1.user.email)
        self.assertTrue(can_access(TEST_USER_EMAIL, TEST_LOCATION))

    def test_grant_access_to_deleted_location(self):
        user = self.users_collection.create_item(TEST_USER_EMAIL)
        location = self.locations_collection.create_item(TEST_LOCATION)
        self.assertTrue(self.locations_collection.delete_item(location.uuid))
        self.assertRaises(ValidationError,
                          location.grant_access,
                          user.uuid)

    def test_revoke_access(self):
        user = self.users_collection.create_item(TEST_USER_EMAIL)
        location = self.locations_collection.create_item(TEST_LOCATION)
        location.grant_access(user.uuid)
        self.assertTrue(can_access(TEST_USER_EMAIL, TEST_LOCATION))
        location.revoke_access(user.uuid)
        self.assertFalse(can_access(TEST_USER_EMAIL, TEST_LOCATION))

    def test_revoke_not_granted_access(self):
        location = self.locations_collection.create_item(TEST_LOCATION)
        user = self.users_collection.create_item(TEST_USER_EMAIL)
        self.assertRaisesRegexp(LookupError,
                                'User can not access location.',
                                location.revoke_access,
                                user.uuid)

    def test_revoke_access_to_deleted_location(self):
        user = self.users_collection.create_item(TEST_USER_EMAIL)
        location = self.locations_collection.create_item(TEST_LOCATION)
        location.grant_access(user.uuid)
        self.assertTrue(self.locations_collection.delete_item(location.uuid))
        self.assertRaisesRegexp(LookupError,
                                'User can not access location.',
                                location.revoke_access,
                                user.uuid)

    def test_revoke_access_for_not_existing_user(self):
        location = self.locations_collection.create_item(TEST_LOCATION)
        self.assertRaisesRegexp(LookupError,
                                'User not found',
                                location.revoke_access,
                                FAKE_UUID)

    def test_grant_access_gives_access_to_sublocations(self):
        location = self.locations_collection.create_item('/foo/bar')
        user = self.users_collection.create_item('foo@example.com')
        location.grant_access(user.uuid)

        self.assertTrue(can_access('foo@example.com', '/foo/bar'))
        self.assertTrue(can_access('foo@example.com', '/foo/bar/'))
        self.assertTrue(can_access('foo@example.com', '/foo/bar/b'))
        self.assertTrue(can_access('foo@example.com', '/foo/bar/baz'))
        self.assertTrue(can_access('foo@example.com', '/foo/bar/baz/bar/'))

        self.assertFalse(can_access('foo@example.com', '/foo/ba'))
        self.assertFalse(can_access('foo@example.com', '/foo/barr'))
        self.assertFalse(can_access('foo@example.com', '/foo/foo/bar'))

    def test_more_specific_location_takes_precedence_over_generic(self):
        location = self.locations_collection.create_item('/foo/bar')
        user = self.users_collection.create_item('foo@example.com')
        location.grant_access(user.uuid)

        self.locations_collection.create_item('/foo/bar/baz')
        self.assertTrue(can_access('foo@example.com', '/foo/bar'))
        self.assertTrue(can_access('foo@example.com', '/foo/bar/ba'))
        self.assertTrue(can_access('foo@example.com', '/foo/bar/bazz'))

        self.assertFalse(can_access('foo@example.com', '/foo/bar/baz'))
        self.assertFalse(can_access('foo@example.com', '/foo/bar/baz/'))
        self.assertFalse(can_access('foo@example.com', '/foo/bar/baz/bam'))

    # TODO: it should rather not be ignored?
    def test_trailing_slash_ignored(self):
        # TODO: what about this / here.
        location = self.locations_collection.create_item('/foo/bar/')
        user = self.users_collection.create_item('foo@example.com')
        location.grant_access(user.uuid)

        self.assertTrue(can_access('foo@example.com', '/foo/bar'))
        self.assertTrue(can_access('foo@example.com', '/foo/bar/'))

        self.assertFalse(can_access('foo@example.com', '/foo/barr'))
        self.assertFalse(can_access('foo@example.com', '/foo/ba/'))

    def test_grant_access_to_root(self):
        location = self.locations_collection.create_item('/')
        user = self.users_collection.create_item('foo@example.com')
        location.grant_access(user.uuid)

        self.assertTrue(can_access('foo@example.com', '/'))
        self.assertTrue(can_access('foo@example.com', '/f'))
        self.assertTrue(can_access('foo@example.com', '/foo/bar/baz'))

    def test_get_allowed_users(self):
        location1 = self.locations_collection.create_item('/foo/bar')
        location2 = self.locations_collection.create_item('/foo/baz')

        user1 = self.users_collection.create_item('foo@example.com')
        user2 = self.users_collection.create_item('bar@example.com')
        user3 = self.users_collection.create_item('baz@example.com')

        location1.grant_access(user1.uuid)
        location1.grant_access(user2.uuid)
        location2.grant_access(user3.uuid)

        self.assertItemsEqual(['foo@example.com', 'bar@example.com'],
                              [u['email'] for u in location1.allowed_users()])
        self.assertItemsEqual(['baz@example.com'],
                              [u['email'] for u in location2.allowed_users()])

        location1.revoke_access(user1.uuid)
        self.assertItemsEqual(['bar@example.com'],
                              [u['email'] for u in location1.allowed_users()])

    def test_get_allowed_users_when_empty(self):
        location = self.locations_collection.create_item(TEST_LOCATION)
        self.assertEqual([], location.allowed_users())

    def test_path_validation(self):
        self.assertRaisesRegexp(CreationException,
                                "empty",
                                self.locations_collection.create_item,
                                '')
        self.assertRaisesRegexp(CreationException,
                                "empty",
                                self.locations_collection.create_item,
                                ' ')
        self.assertRaisesRegexp(CreationException,
                                "parameters",
                                self.locations_collection.create_item,
                                '/foo;bar')
        self.assertRaisesRegexp(CreationException,
                                "query",
                                self.locations_collection.create_item,
                                '/foo?s=bar')
        self.assertRaisesRegexp(CreationException,
                                "fragment",
                                self.locations_collection.create_item,
                                '/foo#bar')
        self.assertRaisesRegexp(CreationException,
                                "scheme",
                                self.locations_collection.create_item,
                                'file://foo')
        self.assertRaisesRegexp(CreationException,
                                "domain",
                                self.locations_collection.create_item,
                                'http://example.com/foo')
        self.assertRaisesRegexp(CreationException,
                                "port",
                                self.locations_collection.create_item,
                                'http://example.com:81/foo')
        self.assertRaisesRegexp(CreationException,
                                "username",
                                self.locations_collection.create_item,
                                'http://boo@example.com/foo')
        self.assertRaisesRegexp(CreationException,
                                "normalized",
                                self.locations_collection.create_item,
                                '/foo/./')
        self.assertRaisesRegexp(CreationException,
                                "normalized",
                                self.locations_collection.create_item,
                                '/foo/..')
        self.assertRaisesRegexp(CreationException,
                                "normalized",
                                self.locations_collection.create_item,
                                '/foo/../bar/')
        self.assertRaisesRegexp(CreationException,
                                "normalized",
                                self.locations_collection.create_item,
                                '/foo//bar')
        self.assertRaisesRegexp(CreationException,
                                "normalized",
                                self.locations_collection.create_item,
                                '/foo//')

    def create_location(self, path):
        return self.locations_collection.create_item(path)
    def test_path_encoding(self):
        self.assertEqual('/', self.create_location('/').path)
        self.assertEqual('/foo', self.create_location('/foo').path)
        self.assertEqual('/foo/', self.create_location('/foo/').path)
        self.assertEqual('/foo.', self.create_location('/foo.').path)
        self.assertEqual('/foo..', self.create_location('/foo..').path)
        self.assertEqual('/foo%20bar', self.create_location('/foo bar').path)
        self.assertEqual('/foo~', self.create_location('/foo~').path)
        self.assertEqual('/foo/bar%21%407%2A',
                         self.create_location('/foo/bar!@7*').path)

    # TODO: test that removing user and location revokes access

