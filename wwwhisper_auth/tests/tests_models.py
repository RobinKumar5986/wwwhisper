# coding=utf-8

# wwwhisper - web access control.
# Copyright (C) 2012 Jan Wrobel <wrr@mixedbit.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.forms import ValidationError
from django.test import TestCase
from wwwhisper_auth import models
from wwwhisper_auth.models import CreationException

FAKE_UUID = '41be0192-0fcc-4a9c-935d-69243b75533c'
TEST_SITE = 'https://example.com'
TEST_SITE2 = 'https://example.org'
TEST_USER_EMAIL = 'foo@bar.com'
TEST_LOCATION = '/pub/kika'

class SitesTest(TestCase):
    def test_create_site(self):
        site = models.create_site(TEST_SITE)
        self.assertEqual(TEST_SITE, site.site_id)

    def test_create_site_twice(self):
        site = models.create_site(TEST_SITE)
        self.assertRaisesRegexp(CreationException,
                                'Site already exists.',
                                models.create_site,
                                TEST_SITE)

    def test_find_site(self):
        site1 = models.create_site(TEST_SITE)
        site2 = models.find_site(TEST_SITE)
        self.assertIsNotNone(site2)
        self.assertEqual(site1, site2)

    def test_delete_site(self):
        site1 = models.create_site(TEST_SITE)
        self.assertTrue(models.delete_site(TEST_SITE))
        self.assertIsNone(models.find_site(TEST_SITE))

class CollectionTestCase(TestCase):
    def setUp(self):
        self.locations = models.LocationsCollection(TEST_SITE)
        self.users = models.UsersCollection(TEST_SITE)

class UsersCollectionTest(CollectionTestCase):
    def setUp(self):
        super(UsersCollectionTest, self).setUp()
        models.create_site(TEST_SITE)
        models.create_site(TEST_SITE2)

    def test_create_user(self):
        user = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        self.assertEqual(TEST_USER_EMAIL, user.email)
        self.assertEqual(TEST_SITE, user.get_profile().site_id)

    def test_create_user_non_existing_site(self):
        self.assertRaisesRegexp(CreationException,
                                'Invalid site id.',
                                self.users.create_item,
                                'foo.bar',
                                TEST_USER_EMAIL)

    def test_find_user(self):
        user1 = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        user2 = self.users.find_item(TEST_SITE, user1.uuid)
        self.assertIsNotNone(user2)
        self.assertEqual(user1, user2)

    def test_find_user_different_site(self):
        user1 = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        self.assertIsNone(
            self.users.find_item(TEST_SITE2, user1.uuid))

    def test_find_user_non_existing_site(self):
        user1 = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        self.assertIsNone(self.users.find_item('foo.bar.co', user1.uuid))

    def test_find_user_by_email(self):
        self.assertIsNone(
            self.users.find_item_by_email(TEST_SITE, TEST_USER_EMAIL))
        user1 = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        user2 = self.users.find_item_by_email(TEST_SITE, TEST_USER_EMAIL)
        self.assertIsNotNone(user2)
        self.assertEqual(user1, user2)

    def test_find_user_by_email_different_site(self):
        self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        self.assertIsNone(
            self.users.find_item_by_email(TEST_SITE2, TEST_USER_EMAIL))

    def test_find_user_by_email_non_existing_site(self):
        self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        self.assertIsNone(
            self.users.find_item_by_email('foo.bar.co', TEST_USER_EMAIL))

    def test_find_user_by_email_is_case_insensitive(self):
        user1 = self.users.create_item(TEST_SITE, 'foo@bar.com')
        user2 = self.users.find_item_by_email(TEST_SITE, 'FOo@bar.com')
        self.assertIsNotNone(user2)
        self.assertEqual(user1, user2)

    def test_delete_user(self):
        user = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        self.assertTrue(self.users.delete_item(TEST_SITE, user.uuid))
        self.assertIsNone(self.users.find_item(TEST_SITE, user.uuid))

    def test_create_user_twice(self):
        self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        self.assertRaisesRegexp(CreationException,
                                'User already exists',
                                self.users.create_item,
                                TEST_SITE,
                                TEST_USER_EMAIL)

        # Make sure user lookup is case insensitive.
        self.users.create_item(TEST_SITE, 'uSeR@bar.com')
        self.assertRaisesRegexp(CreationException,
                                'User already exists',
                                self.users.create_item,
                                TEST_SITE,
                                'UsEr@bar.com')

    def test_create_user_twice_for_different_sites(self):
        self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        self.users.create_item(TEST_SITE2, TEST_USER_EMAIL)
        # Should not raise

    def test_delete_user_twice(self):
        user = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        self.assertTrue(self.users.delete_item(TEST_SITE, user.uuid))
        self.assertFalse(self.users.delete_item(TEST_SITE, user.uuid))

    def test_delete_user_different_site(self):
        user = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        self.assertFalse(self.users.delete_item(TEST_SITE2, user.uuid))

    def test_get_all_users(self):
        user1 = self.users.create_item(TEST_SITE, 'foo@example.com')
        user2 = self.users.create_item(TEST_SITE, 'bar@example.com')
        user3 = self.users.create_item(TEST_SITE2, 'baz@example.com')
        self.assertItemsEqual(
            ['foo@example.com', 'bar@example.com'],
            [u.email for u in self.users.all(TEST_SITE)])
        self.users.delete_item(TEST_SITE, user1.uuid)
        self.assertItemsEqual(
            ['bar@example.com'],
            [u.email for u in self.users.all(TEST_SITE)])

    def test_get_all_users_when_empty(self):
        self.assertListEqual([], list(self.users.all(TEST_SITE)))

    def test_email_validation(self):
        """Test strings taken from BrowserId tests."""
        self.assertIsNotNone(self.users.create_item(TEST_SITE, 'x@y.z'))
        self.assertIsNotNone(self.users.create_item(TEST_SITE, 'x@y.z.w'))
        self.assertIsNotNone(self.users.create_item(TEST_SITE, 'x.v@y.z.w'))
        self.assertIsNotNone(self.users.create_item(TEST_SITE, 'x_v@y.z.w'))

        self.assertRaisesRegexp(CreationException,
                                'Invalid email format',
                                self.users.create_item,
                                TEST_SITE,
                                'x')
        self.assertRaisesRegexp(CreationException,
                                'Invalid email format',
                                self.users.create_item,
                                TEST_SITE,
                                'x@y')
        self.assertRaisesRegexp(CreationException,
                                'Invalid email format',
                                self.users.create_item,
                                TEST_SITE,
                                '@y.z')
        self.assertRaisesRegexp(CreationException,
                                'Invalid email format',
                                self.users.create_item,
                                TEST_SITE,
                                'z@y.z@y.z')
        self.assertRaisesRegexp(CreationException,
                                'Invalid email format',
                                self.users.create_item,
                                TEST_SITE,
                                '')

    def test_email_normalization(self):
        email = self.users.create_item(TEST_SITE, 'x@y.z').email
        self.assertEqual('x@y.z', email)

        email = self.users.create_item(TEST_SITE, 'aBc@y.z').email
        self.assertEqual('abc@y.z', email)

class LocationsCollectionTest(CollectionTestCase):
    def setUp(self):
        super(LocationsCollectionTest, self).setUp()
        models.create_site(TEST_SITE)
        models.create_site(TEST_SITE2)

    def test_create_location(self):
        location = self.locations.create_item(TEST_SITE, TEST_LOCATION)
        self.assertEqual(TEST_LOCATION, location.path)
        self.assertEqual(TEST_SITE, location.site_id)

    def test_create_location_non_existing_site(self):
        self.assertRaisesRegexp(CreationException,
                                'Invalid site id.',
                                self.locations.create_item,
                                'foo.co.uk',
                                TEST_LOCATION)

    def test_find_location_by_id(self):
        location1 = self.locations.create_item(TEST_SITE, TEST_LOCATION)
        location2 = self.locations.find_item(TEST_SITE, location1.uuid)
        self.assertIsNotNone(location2)
        self.assertEqual(location1.path, location2.path)
        self.assertEqual(location1.uuid, location2.uuid)

    def test_delete_location(self):
        location = self.locations.create_item(TEST_SITE, TEST_LOCATION)
        self.assertIsNotNone(self.locations.find_item(TEST_SITE, location.uuid))
        self.assertTrue(self.locations.delete_item(TEST_SITE, location.uuid))
        self.assertIsNone(self.locations.find_item(TEST_SITE, location.uuid))

    def test_create_location_twice(self):
        self.locations.create_item(TEST_SITE, TEST_LOCATION)
        self.assertRaisesRegexp(CreationException,
                                'Location already exists',
                                self.locations.create_item,
                                TEST_SITE,
                                TEST_LOCATION)

    def test_create_location_twice_for_different_sites(self):
        self.locations.create_item(TEST_SITE, TEST_LOCATION)
        self.locations.create_item(TEST_SITE2, TEST_LOCATION)

    def test_delete_location_twice(self):
        location = self.locations.create_item(TEST_SITE, TEST_LOCATION)
        self.assertTrue(self.locations.delete_item(TEST_SITE, location.uuid))
        self.assertFalse(self.locations.delete_item(TEST_SITE, location.uuid))

    def test_get_all_locations(self):
        location1 = self.locations.create_item(TEST_SITE, '/foo')
        location2 = self.locations.create_item(TEST_SITE, '/foo/bar')
        self.locations.create_item(TEST_SITE2, '/foo/baz')
        self.assertItemsEqual(['/foo/bar', '/foo'],
                              [l.path for l
                               in self.locations.all(TEST_SITE)])
        self.locations.delete_item(TEST_SITE, location1.uuid)
        self.assertItemsEqual(['/foo/bar'],
                              [l.path for l
                               in self.locations.all(TEST_SITE)])

    def test_get_all_locations_when_empty(self):
        self.assertListEqual([], list(self.locations.all(TEST_SITE)))

    def test_grant_access(self):
        user = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        location = self.locations.create_item(TEST_SITE, TEST_LOCATION)
        self.assertFalse(location.can_access(user))
        (perm, created) = location.grant_access(user.uuid)
        self.assertTrue(created)
        self.assertIsNotNone(perm)
        self.assertTrue(location.can_access(user))

    def test_grant_access_for_not_existing_user(self):
        location = self.locations.create_item(TEST_SITE, TEST_LOCATION)
        self.assertRaisesRegexp(LookupError,
                                'User not found',
                                location.grant_access,
                                FAKE_UUID)

    def test_grant_access_for_user_of_different_site(self):
        user = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        location = self.locations.create_item(TEST_SITE2, TEST_LOCATION)
        self.assertFalse(location.can_access(user))
        self.assertRaisesRegexp(LookupError,
                                'User not found',
                                location.grant_access,
                                user.uuid)

    def test_user_of_different_site_can_not_access_even_if_open_location(self):
        user = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        location = self.locations.create_item(TEST_SITE2, TEST_LOCATION)
        location.grant_open_access(require_login=True)
        self.assertFalse(location.can_access(user))

    def test_grant_access_if_already_granted(self):
        location = self.locations.create_item(TEST_SITE, TEST_LOCATION)
        user = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        (permission1, created1) = location.grant_access(user.uuid)
        self.assertTrue(created1)
        (permission2, created2) = location.grant_access(user.uuid)
        self.assertFalse(created2)
        self.assertEqual(permission1, permission2)
        self.assertEqual(TEST_USER_EMAIL, permission1.user.email)
        self.assertTrue(location.can_access(user))

    def test_grant_access_to_deleted_location(self):
        user = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        location = self.locations.create_item(TEST_SITE, TEST_LOCATION)
        self.assertTrue(self.locations.delete_item(TEST_SITE, location.uuid))
        self.assertRaises(ValidationError,
                          location.grant_access,
                          user.uuid)

    def test_revoke_access(self):
        user = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        location = self.locations.create_item(TEST_SITE, TEST_LOCATION)
        location.grant_access(user.uuid)
        self.assertTrue(location.can_access(user))
        location.revoke_access(user.uuid)
        self.assertFalse(location.can_access(user))

    def test_revoke_not_granted_access(self):
        location = self.locations.create_item(TEST_SITE, TEST_LOCATION)
        user = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        self.assertRaisesRegexp(LookupError,
                                'User can not access location.',
                                location.revoke_access,
                                user.uuid)

    def test_revoke_access_to_deleted_location(self):
        user = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        location = self.locations.create_item(TEST_SITE, TEST_LOCATION)
        location.grant_access(user.uuid)
        self.assertTrue(self.locations.delete_item(TEST_SITE, location.uuid))
        self.assertRaisesRegexp(LookupError,
                                'User can not access location.',
                                location.revoke_access,
                                user.uuid)

    def test_deleting_user_revokes_access(self):
        user = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        location = self.locations.create_item(TEST_SITE, TEST_LOCATION)
        self.assertFalse(location.can_access(user))
        location.grant_access(user.uuid)
        self.assertTrue(location.can_access(user))
        self.users.delete_item(TEST_SITE, user.uuid)
        self.assertFalse(location.can_access(user))

    def test_deleting_location_revokes_access(self):
        user = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        location = self.locations.create_item(TEST_SITE, TEST_LOCATION)
        self.assertFalse(location.can_access(user))
        location.grant_access(user.uuid)
        self.assertTrue(location.can_access(user))
        self.locations.delete_item(TEST_SITE, location.uuid)
        self.assertFalse(location.can_access(user))

    def test_revoke_access_for_not_existing_user(self):
        location = self.locations.create_item(TEST_SITE, TEST_LOCATION)
        self.assertRaisesRegexp(LookupError,
                                'User not found',
                                location.revoke_access,
                                FAKE_UUID)

    def test_get_permission(self):
        location = self.locations.create_item(TEST_SITE, TEST_LOCATION)
        user1 = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        self.assertRaisesRegexp(LookupError,
                                'User can not access',
                                location.get_permission,
                                user1.uuid)
        location.grant_access(user1.uuid)
        self.assertIsNotNone(location.get_permission(user1.uuid))

        user2 = self.users.create_item(TEST_SITE2, TEST_USER_EMAIL)
        # User does not belong to the site.
        self.assertRaisesRegexp(LookupError,
                                'User not found',
                                location.get_permission,
                                user2.uuid)

    def test_find_location_by_path(self):
        location = self.locations.create_item(TEST_SITE, '/foo/bar')
        self.assertEqual(
            location, self.locations.find_location(TEST_SITE, '/foo/bar'))
        self.assertIsNone(self.locations.find_location(TEST_SITE2, '/foo/bar'))

        self.assertEqual(
            location, self.locations.find_location(TEST_SITE, '/foo/bar/'))
        self.assertIsNone(self.locations.find_location(TEST_SITE2, '/foo/bar/'))

        self.assertEqual(
            location, self.locations.find_location(TEST_SITE, '/foo/bar/b'))
        self.assertIsNone(
            self.locations.find_location(TEST_SITE2, '/foo/bar/b'))

        self.assertEqual(
            location, self.locations.find_location(TEST_SITE, '/foo/bar/baz'))
        self.assertIsNone(
            self.locations.find_location(TEST_SITE2, '/foo/bar/baz'))

        self.assertEqual(
            location,
            self.locations.find_location(TEST_SITE, '/foo/bar/baz/bar/'))
        self.assertIsNone(
            self.locations.find_location(TEST_SITE2, '/foo/bar/baz/bar/'))

        self.assertIsNone(self.locations.find_location(TEST_SITE, '/foo/ba'))
        self.assertIsNone(self.locations.find_location(TEST_SITE, '/foo/barr'))
        self.assertIsNone(
            self.locations.find_location(TEST_SITE, '/foo/foo/bar'))

    def test_more_specific_location_takes_precedence_over_generic(self):
        location1 = self.locations.create_item(TEST_SITE, '/foo/bar')
        user = self.users.create_item(TEST_SITE, 'foo@example.com')
        location1.grant_access(user.uuid)

        location2 = self.locations.create_item(TEST_SITE, '/foo/bar/baz')
        self.assertEqual(
            location1, self.locations.find_location(TEST_SITE, '/foo/bar'))
        self.assertEqual(
            location1, self.locations.find_location(TEST_SITE, '/foo/bar/ba'))
        self.assertEqual(
            location1, self.locations.find_location(TEST_SITE, '/foo/bar/bazz'))

        self.assertEqual(
            location2, self.locations.find_location(TEST_SITE, '/foo/bar/baz'))
        self.assertEqual(
            location2, self.locations.find_location(TEST_SITE, '/foo/bar/baz/'))
        self.assertEqual(
            location2,
            self.locations.find_location(TEST_SITE, '/foo/bar/baz/bam'))
        self.assertFalse(location2.can_access(user))

    def test_trailing_slash_respected(self):
        location = self.locations.create_item(TEST_SITE, '/foo/bar/')
        self.assertIsNone(self.locations.find_location(TEST_SITE, '/foo/bar'))

    def test_grant_access_to_root(self):
        location = self.locations.create_item(TEST_SITE, '/')
        user = self.users.create_item(TEST_SITE, 'foo@example.com')
        location.grant_access(user.uuid)

        self.assertEqual(location, self.locations.find_location(TEST_SITE, '/'))
        self.assertEqual(
            location, self.locations.find_location(TEST_SITE, '/f'))
        self.assertEqual(
            location, self.locations.find_location(TEST_SITE, '/foo/bar/baz'))

    def test_grant_open_access(self):
        user = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        location = self.locations.create_item(TEST_SITE, TEST_LOCATION)
        self.assertFalse(location.open_access_granted())
        self.assertFalse(location.open_access_requires_login())
        self.assertFalse(location.can_access(user))

        location.grant_open_access(require_login=False)
        self.assertTrue(location.open_access_granted())
        self.assertFalse(location.open_access_requires_login())
        self.assertTrue(location.can_access(user))

        location.revoke_open_access()
        self.assertFalse(location.open_access_granted())
        self.assertFalse(location.can_access(user))

    def test_grant_authenticated_open_access(self):
        user = self.users.create_item(TEST_SITE, TEST_USER_EMAIL)
        location = self.locations.create_item(TEST_SITE, TEST_LOCATION)
        self.assertFalse(location.open_access_granted())
        self.assertFalse(location.open_access_requires_login())
        self.assertFalse(location.can_access(user))

        location.grant_open_access(require_login=True)
        self.assertTrue(location.open_access_granted())
        self.assertTrue(location.open_access_requires_login())
        self.assertTrue(location.can_access(user))

        location.revoke_open_access()
        self.assertFalse(location.open_access_granted())
        self.assertFalse(location.can_access(user))

    def test_has_open_location_with_login(self):
        self.assertFalse(self.locations.has_open_location_with_login(TEST_SITE))
        self.locations.create_item(TEST_SITE, '/bar')
        self.assertFalse(self.locations.has_open_location_with_login(TEST_SITE))
        location = self.locations.create_item(TEST_SITE, '/foo')
        location.grant_open_access(False)
        self.assertFalse(self.locations.has_open_location_with_login(TEST_SITE))
        location.grant_open_access(True)
        self.assertTrue(self.locations.has_open_location_with_login(TEST_SITE))
        self.assertFalse(
            self.locations.has_open_location_with_login(TEST_SITE2))

    def test_get_allowed_users(self):
        location1 = self.locations.create_item(TEST_SITE, '/foo/bar')
        location2 = self.locations.create_item(TEST_SITE, '/foo/baz')

        user1 = self.users.create_item(TEST_SITE, 'foo@example.com')
        user2 = self.users.create_item(TEST_SITE, 'bar@example.com')
        user3 = self.users.create_item(TEST_SITE, 'baz@example.com')

        location1.grant_access(user1.uuid)
        location1.grant_access(user2.uuid)
        location2.grant_access(user3.uuid)

        self.assertItemsEqual(['foo@example.com', 'bar@example.com'],
                              [u.email for u in location1.allowed_users()])
        self.assertItemsEqual(['baz@example.com'],
                              [u.email for u in location2.allowed_users()])

        location1.revoke_access(user1.uuid)
        self.assertItemsEqual(['bar@example.com'],
                              [u.email for u in location1.allowed_users()])

    def test_get_allowed_users_when_empty(self):
        location = self.locations.create_item(TEST_SITE, TEST_LOCATION)
        self.assertEqual([], location.allowed_users())

    def test_location_path_validation(self):
        self.assertRaisesRegexp(CreationException,
                                'should be absolute and normalized',
                                self.locations.create_item,
                                TEST_SITE,
                                '/foo/../bar')
        self.assertRaisesRegexp(CreationException,
                                'should not contain parameters',
                                self.locations.create_item,
                                TEST_SITE,
                                '/foo;bar')
        self.assertRaisesRegexp(CreationException,
                                'should not contain query',
                                self.locations.create_item,
                                TEST_SITE,
                                '/foo?s=bar')
        self.assertRaisesRegexp(CreationException,
                                'should not contain fragment',
                                self.locations.create_item,
                                TEST_SITE,
                                '/foo#bar')
        self.assertRaisesRegexp(CreationException,
                                'should contain only ascii',
                                self.locations.create_item,
                                TEST_SITE,
                                u'/żbik')

    """Path passed to create_location is expected to be saved verbatim."""
    def test_location_path_not_encoded(self):
        self.assertEqual(
            '/foo%20bar',
            self.locations.create_item(TEST_SITE, '/foo%20bar').path)
        self.assertEqual(
            '/foo~',
            self.locations.create_item(TEST_SITE, '/foo~').path)
        self.assertEqual(
            '/foo/bar!@7*',
            self.locations.create_item(TEST_SITE, '/foo/bar!@7*').path)

