# coding=utf-8

# wwwhisper - web access control.
# Copyright (C) 2012, 2013 Jan Wrobel <wrr@mixedbit.org>
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
from contextlib import contextmanager
from functools import wraps
from wwwhisper_auth import models

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
        self.assertRaisesRegexp(ValidationError,
                                'Site .* already exists.',
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
        self.site = models.create_site(TEST_SITE)
        self.locations = self.site.locations
        self.users = self.site.users

    @contextmanager
    def assert_site_modified(self, site):
        mod_id = site.mod_id
        yield
        self.assertNotEqual(mod_id, site.mod_id)

    @contextmanager
    def assert_site_not_modified(self, site):
        mod_id = site.mod_id
        yield
        self.assertEqual(mod_id,  site.mod_id)

# Test testing infrastructure.
class SiteModifiedTest(CollectionTestCase):
    def test_assert_site_modified(self):
        with self.assert_site_modified(self.site):
            self.site.site_modified()
        # Should not raise anything

    def test_assert_site_not_modified(self):
        with self.assert_site_not_modified(self.site):
            pass
        # Should not raise anything

    def test_assert_site_modified_raises(self):
        try:
            with self.assert_site_modified(self.site):
                pass
        except AssertionError as er:
            pass # Expected.
        else:
            self.fail('Assertion not raised')

    def test_assert_site_not_modified_raises(self):
        try:
            with self.assert_site_not_modified(self.site):
                self.site.site_modified()
        except AssertionError as er:
            pass # Expected.
        else:
            self.fail('Assertion not raised')

class UsersCollectionTest(CollectionTestCase):
    def setUp(self):
        super(UsersCollectionTest, self).setUp()
        self.site2 = models.create_site(TEST_SITE2)

    def test_create_user(self):
        with self.assert_site_modified(self.site):
            user = self.users.create_item(TEST_USER_EMAIL)
        self.assertEqual(TEST_USER_EMAIL, user.email)
        self.assertEqual(TEST_SITE, user.get_profile().site_id)

    def test_create_user_non_existing_site(self):
        self.assertTrue(models.delete_site(self.site.site_id))
        self.assertRaisesRegexp(ValidationError,
                                'site no longer exists.',
                                self.users.create_item,
                                TEST_USER_EMAIL)

    def test_find_user(self):
        user1 = self.users.create_item(TEST_USER_EMAIL)
        with self.assert_site_not_modified(self.site):
            user2 = self.users.find_item(user1.uuid)
        self.assertIsNotNone(user2)
        self.assertEqual(user1, user2)

    def test_find_user_different_site(self):
        user1 = self.users.create_item(TEST_USER_EMAIL)
        self.assertIsNone(self.site2.users.find_item(user1.uuid))

    def test_find_user_non_existing_site(self):
        user = self.users.create_item(TEST_USER_EMAIL)
        uuid = user.uuid
        self.assertTrue(models.delete_site(self.site.site_id))
        self.assertIsNone(self.users.find_item(uuid))

    def test_delete_site_deletes_user(self):
        user = self.users.create_item(TEST_USER_EMAIL)
        self.assertEqual(1, user.__class__.objects.filter(id=user.id).count())
        self.assertTrue(models.delete_site(self.site.site_id))
        self.assertEqual(0, user.__class__.objects.filter(id=user.id).count())

    def test_find_user_by_email(self):
        self.assertIsNone(self.users.find_item_by_email(TEST_USER_EMAIL))
        user1 = self.users.create_item(TEST_USER_EMAIL)
        with self.assert_site_not_modified(self.site):
            user2 = self.users.find_item_by_email(TEST_USER_EMAIL)
        self.assertIsNotNone(user2)
        self.assertEqual(user1, user2)

    def test_find_user_by_email_different_site(self):
        self.users.create_item(TEST_USER_EMAIL)
        self.assertIsNone(self.site2.users.find_item_by_email(TEST_USER_EMAIL))

    def test_find_user_by_email_non_existing_site(self):
        self.users.create_item(TEST_USER_EMAIL)
        self.assertTrue(models.delete_site(self.site.site_id))
        self.assertIsNone(self.users.find_item_by_email(TEST_USER_EMAIL))

    def test_find_user_by_email_is_case_insensitive(self):
        user1 = self.users.create_item('foo@bar.com')
        user2 = self.users.find_item_by_email('FOo@bar.com')
        self.assertIsNotNone(user2)
        self.assertEqual(user1, user2)

    def test_delete_user(self):
        user = self.users.create_item(TEST_USER_EMAIL)
        with self.assert_site_modified(self.site):
            self.assertTrue(self.users.delete_item(user.uuid))
        self.assertIsNone(self.users.find_item(user.uuid))

    def test_create_user_twice(self):
        self.users.create_item(TEST_USER_EMAIL)
        self.assertRaisesRegexp(ValidationError,
                                'User already exists',
                                self.users.create_item,
                                TEST_USER_EMAIL)

        # Make sure user lookup is case insensitive.
        self.users.create_item('uSeR@bar.com')
        with self.assert_site_not_modified(self.site):
            self.assertRaisesRegexp(ValidationError,
                                    'User already exists',
                                    self.users.create_item,
                                    'UsEr@bar.com')

    def test_create_user_twice_for_different_sites(self):
        self.users.create_item(TEST_USER_EMAIL)
        with self.assert_site_not_modified(self.site):
            with self.assert_site_modified(self.site2):
                self.site2.users.create_item(TEST_USER_EMAIL)
        # Should not raise

    def test_delete_user_twice(self):
        user = self.users.create_item(TEST_USER_EMAIL)
        self.assertTrue(self.users.delete_item(user.uuid))
        self.assertFalse(self.users.delete_item(user.uuid))

    def test_delete_user_different_site(self):
        user = self.users.create_item(TEST_USER_EMAIL)
        self.assertFalse(self.site2.users.delete_item(user.uuid))

    def test_get_all_users(self):
        user1 = self.users.create_item('foo@example.com')
        user2 = self.users.create_item('bar@example.com')
        user3 = self.site2.users.create_item('baz@example.com')
        with self.assert_site_not_modified(self.site):
            self.assertItemsEqual(
                ['foo@example.com', 'bar@example.com'],
                [u.email for u in self.users.all()])
        self.users.delete_item(user1.uuid)
        self.assertItemsEqual(
            ['bar@example.com'],
            [u.email for u in self.users.all()])

    def test_get_all_users_when_empty(self):
        self.assertListEqual([], list(self.users.all()))

    def test_email_validation(self):
        """Test strings taken from BrowserId tests."""
        self.assertIsNotNone(self.users.create_item('x@y.z'))
        self.assertIsNotNone(self.users.create_item('x@y.z.w'))
        self.assertIsNotNone(self.users.create_item('x.v@y.z.w'))
        self.assertIsNotNone(self.users.create_item('x_v@y.z.w'))
        # Valid tricky characters.
        self.assertIsNotNone(self.users.create_item(
                r'x#!v$we*df+.|{}@y132.wp.a-s.012'))

        with self.assert_site_not_modified(self.site):
            self.assertRaisesRegexp(ValidationError,
                                    'Invalid email format',
                                    self.users.create_item,
                                    'x')
            self.assertRaisesRegexp(ValidationError,
                                    'Invalid email format',
                                    self.users.create_item,
                                    'x@y')
            self.assertRaisesRegexp(ValidationError,
                                    'Invalid email format',
                                    self.users.create_item,
                                    '@y.z')
            self.assertRaisesRegexp(ValidationError,
                                    'Invalid email format',
                                    self.users.create_item,
                                    'z@y.z@y.z')
            self.assertRaisesRegexp(ValidationError,
                                    'Invalid email format',
                                    self.users.create_item,
                                    '')
            # Invalid tricky character.
            self.assertRaisesRegexp(ValidationError,
                                    'Invalid email format',
                                    self.users.create_item,
                                    r'a\b@b.c.d')
            # Too long.
            self.assertRaisesRegexp(ValidationError,
                                    'Invalid email format',
                                    self.users.create_item,
                                    'foo@bar.com.' + ('z' * 100) )

    def test_email_normalization(self):
        email = self.users.create_item('x@y.z').email
        self.assertEqual('x@y.z', email)

        email = self.users.create_item('aBc@y.z').email
        self.assertEqual('abc@y.z', email)

class LocationsCollectionTest(CollectionTestCase):
    def setUp(self):
        super(LocationsCollectionTest, self).setUp()
        self.site2 = models.create_site(TEST_SITE2)

    def test_create_location(self):
        with self.assert_site_modified(self.site):
            location = self.locations.create_item(TEST_LOCATION)
            self.assertEqual(TEST_LOCATION, location.path)
            self.assertEqual(TEST_SITE, location.site_id)

    def test_create_location_non_existing_site(self):
        self.assertTrue(models.delete_site(self.site.site_id))
        self.assertRaisesRegexp(ValidationError,
                                'site.*does not exist',
                                self.locations.create_item,
                                TEST_LOCATION)

    def test_delete_site_deletes_location(self):
        location = self.locations.create_item(TEST_LOCATION)
        self.assertEqual(
            1, location.__class__.objects.filter(id=location.id).count())
        self.assertTrue(models.delete_site(self.site.site_id))
        self.assertEqual(
            0, location.__class__.objects.filter(id=location.id).count())

    def test_find_location_by_id(self):
        location1 = self.locations.create_item(TEST_LOCATION)
        with self.assert_site_not_modified(self.site):
            location2 = self.locations.find_item(location1.uuid)
        self.assertIsNotNone(location2)
        self.assertEqual(location1.path, location2.path)
        self.assertEqual(location1.uuid, location2.uuid)

    def test_delete_location(self):
        location = self.locations.create_item(TEST_LOCATION)
        self.assertIsNotNone(self.locations.find_item(location.uuid))
        with self.assert_site_modified(self.site):
            self.assertTrue(self.locations.delete_item(location.uuid))
        self.assertIsNone(self.locations.find_item(location.uuid))

    def test_create_location_twice(self):
        self.locations.create_item(TEST_LOCATION)
        with self.assert_site_not_modified(self.site):
            self.assertRaisesRegexp(ValidationError,
                                    'Location already exists',
                                    self.locations.create_item,
                                    TEST_LOCATION)

    def test_create_location_twice_for_different_sites(self):
        self.locations.create_item(TEST_LOCATION)
        with self.assert_site_not_modified(self.site):
            with self.assert_site_modified(self.site2):
                self.site2.locations.create_item(TEST_LOCATION)

    def test_delete_location_twice(self):
        location = self.locations.create_item(TEST_LOCATION)
        self.assertTrue(self.locations.delete_item(location.uuid))
        self.assertFalse(self.locations.delete_item(location.uuid))

    def test_get_all_locations(self):
        location1 = self.locations.create_item('/foo')
        location2 = self.locations.create_item('/foo/bar')
        self.site2.locations.create_item('/foo/baz')
        with self.assert_site_not_modified(self.site):
            self.assertItemsEqual(['/foo/bar', '/foo'],
                                  [l.path for l
                                   in self.locations.all()])
        self.locations.delete_item(location1.uuid)
        self.assertItemsEqual(['/foo/bar'],
                              [l.path for l
                               in self.locations.all()])

    def test_get_all_locations_when_empty(self):
        self.assertListEqual([], list(self.locations.all()))

    def test_grant_access(self):
        user = self.users.create_item(TEST_USER_EMAIL)
        location = self.locations.create_item(TEST_LOCATION)
        with self.assert_site_not_modified(self.site):
            self.assertFalse(location.can_access(user))
        with self.assert_site_modified(self.site):
            (perm, created) = location.grant_access(user.uuid)
        self.assertTrue(created)
        self.assertIsNotNone(perm)
        self.assertTrue(location.can_access(user))

    def test_grant_access_for_not_existing_user(self):
        location = self.locations.create_item(TEST_LOCATION)
        self.assertRaisesRegexp(LookupError,
                                'User not found',
                                location.grant_access,
                                FAKE_UUID)

    def test_grant_access_for_user_of_different_site(self):
        user = self.users.create_item(TEST_USER_EMAIL)
        location = self.site2.locations.create_item(TEST_LOCATION)
        self.assertFalse(location.can_access(user))
        self.assertRaisesRegexp(LookupError,
                                'User not found',
                                location.grant_access,
                                user.uuid)

    def test_grant_access_if_already_granted(self):
        location = self.locations.create_item(TEST_LOCATION)
        user = self.users.create_item(TEST_USER_EMAIL)
        (permission1, created1) = location.grant_access(user.uuid)
        self.assertTrue(created1)
        (permission2, created2) = location.grant_access(user.uuid)
        self.assertFalse(created2)
        self.assertEqual(permission1, permission2)
        self.assertEqual(TEST_USER_EMAIL, permission1.user.email)
        self.assertTrue(location.can_access(user))

    def test_grant_access_to_deleted_location(self):
        user = self.users.create_item(TEST_USER_EMAIL)
        location = self.locations.create_item(TEST_LOCATION)
        self.assertTrue(self.locations.delete_item(location.uuid))
        self.assertRaises(ValidationError,
                          location.grant_access,
                          user.uuid)

    def test_revoke_access(self):
        user = self.users.create_item(TEST_USER_EMAIL)
        location = self.locations.create_item(TEST_LOCATION)
        location.grant_access(user.uuid)
        self.assertTrue(location.can_access(user))
        with self.assert_site_modified(self.site):
            location.revoke_access(user.uuid)
        self.assertFalse(location.can_access(user))

    def test_revoke_not_granted_access(self):
        location = self.locations.create_item(TEST_LOCATION)
        user = self.users.create_item(TEST_USER_EMAIL)
        with self.assert_site_not_modified(self.site):
            self.assertRaisesRegexp(LookupError,
                                    'User can not access location.',
                                    location.revoke_access,
                                    user.uuid)

    def test_revoke_access_to_deleted_location(self):
        user = self.users.create_item(TEST_USER_EMAIL)
        location = self.locations.create_item(TEST_LOCATION)
        location.grant_access(user.uuid)
        self.assertTrue(self.locations.delete_item(location.uuid))
        self.assertRaisesRegexp(LookupError,
                                'User can not access location.',
                                location.revoke_access,
                                user.uuid)

    def test_deleting_user_revokes_access(self):
        user = self.users.create_item(TEST_USER_EMAIL)
        location = self.locations.create_item(TEST_LOCATION)
        self.assertFalse(location.can_access(user))
        location.grant_access(user.uuid)
        self.assertTrue(location.can_access(user))
        self.users.delete_item(user.uuid)
        self.assertFalse(location.can_access(user))

    def test_deleting_location_revokes_access(self):
        user = self.users.create_item(TEST_USER_EMAIL)
        location = self.locations.create_item(TEST_LOCATION)
        self.assertFalse(location.can_access(user))
        location.grant_access(user.uuid)
        self.assertTrue(location.can_access(user))
        self.locations.delete_item(location.uuid)
        self.assertFalse(location.can_access(user))

    def test_revoke_access_for_not_existing_user(self):
        location = self.locations.create_item(TEST_LOCATION)
        self.assertRaisesRegexp(LookupError,
                                'User not found',
                                location.revoke_access,
                                FAKE_UUID)

    def test_get_permission(self):
        location = self.locations.create_item(TEST_LOCATION)
        user1 = self.users.create_item(TEST_USER_EMAIL)
        self.assertRaisesRegexp(LookupError,
                                'User can not access',
                                location.get_permission,
                                user1.uuid)
        location.grant_access(user1.uuid)
        self.assertIsNotNone(location.get_permission(user1.uuid))

        user2 = self.site2.users.create_item(TEST_USER_EMAIL)
        # User does not belong to the site.
        self.assertRaisesRegexp(LookupError,
                                'User not found',
                                location.get_permission,
                                user2.uuid)

    def test_find_location_by_path(self):
        location = self.locations.create_item('/foo/bar')
        with self.assert_site_not_modified(self.site):
            self.assertEqual(location, self.locations.find_location('/foo/bar'))
            self.assertIsNone(self.site2.locations.find_location('/foo/bar'))

        self.assertEqual(
            location, self.locations.find_location('/foo/bar/'))
        self.assertIsNone(self.site2.locations.find_location('/foo/bar/'))

        self.assertEqual(
            location, self.locations.find_location('/foo/bar/b'))
        self.assertIsNone(self.site2.locations.find_location('/foo/bar/b'))

        self.assertEqual(
            location, self.locations.find_location('/foo/bar/baz'))
        self.assertIsNone(self.site2.locations.find_location('/foo/bar/baz'))

        self.assertEqual(
            location, self.locations.find_location('/foo/bar/baz/bar/'))
        self.assertIsNone(
            self.site2.locations.find_location('/foo/bar/baz/bar/'))

        self.assertIsNone(self.locations.find_location('/foo/ba'))
        self.assertIsNone(self.locations.find_location('/foo/barr'))
        self.assertIsNone(self.locations.find_location('/foo/foo/bar'))

    def test_more_specific_location_takes_precedence_over_generic(self):
        location1 = self.locations.create_item('/foo/bar')
        user = self.users.create_item('foo@example.com')
        location1.grant_access(user.uuid)

        location2 = self.locations.create_item('/foo/bar/baz')
        self.assertEqual(
            location1, self.locations.find_location('/foo/bar'))
        self.assertEqual(
            location1, self.locations.find_location('/foo/bar/ba'))
        self.assertEqual(
            location1, self.locations.find_location('/foo/bar/bazz'))

        self.assertEqual(
            location2, self.locations.find_location('/foo/bar/baz'))
        self.assertEqual(
            location2, self.locations.find_location('/foo/bar/baz/'))
        self.assertEqual(
            location2, self.locations.find_location('/foo/bar/baz/bam'))
        self.assertFalse(location2.can_access(user))

    def test_trailing_slash_respected(self):
        location = self.locations.create_item('/foo/bar/')
        self.assertIsNone(self.locations.find_location('/foo/bar'))

    def test_grant_access_to_root(self):
        location = self.locations.create_item('/')
        user = self.users.create_item('foo@example.com')
        location.grant_access(user.uuid)

        self.assertEqual(location, self.locations.find_location('/'))
        self.assertEqual(location, self.locations.find_location('/f'))
        self.assertEqual(
            location, self.locations.find_location('/foo/bar/baz'))

    def test_grant_open_access(self):
        user = self.users.create_item(TEST_USER_EMAIL)
        location = self.locations.create_item(TEST_LOCATION)
        self.assertFalse(location.open_access_granted())
        self.assertFalse(location.open_access_requires_login())
        self.assertFalse(location.can_access(user))

        with self.assert_site_modified(self.site):
            location.grant_open_access(require_login=False)
        with self.assert_site_not_modified(self.site):
            self.assertTrue(location.open_access_granted())
            self.assertFalse(location.open_access_requires_login())
            self.assertTrue(location.can_access(user))

        with self.assert_site_modified(self.site):
            location.revoke_open_access()
        self.assertFalse(location.open_access_granted())
        self.assertFalse(location.can_access(user))

    def test_user_of_different_site_can_not_access_even_if_open_location(self):
        user = self.users.create_item(TEST_USER_EMAIL)
        location = self.site2.locations.create_item(TEST_LOCATION)
        location.grant_open_access(require_login=True)
        self.assertFalse(location.can_access(user))

    def test_grant_authenticated_open_access(self):
        user = self.users.create_item(TEST_USER_EMAIL)
        location = self.locations.create_item(TEST_LOCATION)
        self.assertFalse(location.open_access_granted())
        self.assertFalse(location.open_access_requires_login())
        self.assertFalse(location.can_access(user))

        with self.assert_site_modified(self.site):
            location.grant_open_access(require_login=True)
        self.assertTrue(location.open_access_granted())
        self.assertTrue(location.open_access_requires_login())
        self.assertTrue(location.can_access(user))

        location.revoke_open_access()
        self.assertFalse(location.open_access_granted())
        self.assertFalse(location.can_access(user))

    def test_has_open_location_with_login(self):
        self.assertFalse(self.locations.has_open_location_with_login())
        self.locations.create_item('/bar')
        self.assertFalse(self.locations.has_open_location_with_login())
        location = self.locations.create_item('/foo')
        location.grant_open_access(False)
        self.assertFalse(self.locations.has_open_location_with_login())
        location.grant_open_access(True)
        self.assertTrue(self.locations.has_open_location_with_login())
        self.assertFalse(self.site2.locations.has_open_location_with_login())

    def test_get_allowed_users(self):
        location1 = self.locations.create_item('/foo/bar')
        location2 = self.locations.create_item('/foo/baz')

        user1 = self.users.create_item('foo@example.com')
        user2 = self.users.create_item('bar@example.com')
        user3 = self.users.create_item('baz@example.com')

        location1.grant_access(user1.uuid)
        location1.grant_access(user2.uuid)
        location2.grant_access(user3.uuid)

        with self.assert_site_not_modified(self.site):
            self.assertItemsEqual(['foo@example.com', 'bar@example.com'],
                                  [u.email for u in location1.allowed_users()])
            self.assertItemsEqual(['baz@example.com'],
                                  [u.email for u in location2.allowed_users()])

        location1.revoke_access(user1.uuid)
        self.assertItemsEqual(['bar@example.com'],
                              [u.email for u in location1.allowed_users()])

    def test_get_allowed_users_when_empty(self):
        location = self.locations.create_item(TEST_LOCATION)
        self.assertEqual([], location.allowed_users())

    def test_location_path_validation(self):
        with self.assert_site_not_modified(self.site):
            self.assertRaisesRegexp(ValidationError,
                                    'should be absolute and normalized',
                                    self.locations.create_item,
                                    '/foo/../bar')
            self.assertRaisesRegexp(ValidationError,
                                    'should not contain parameters',
                                    self.locations.create_item,
                                    '/foo;bar')
            self.assertRaisesRegexp(ValidationError,
                                    'should not contain query',
                                    self.locations.create_item,
                                    '/foo?s=bar')
            self.assertRaisesRegexp(ValidationError,
                                    'should not contain fragment',
                                    self.locations.create_item,
                                    '/foo#bar')
            self.assertRaisesRegexp(ValidationError,
                                    'should contain only ascii',
                                    self.locations.create_item,
                                    u'/żbik')
            long_path = '/a' * (self.locations.path_len_limit / 2) + 'a'
            self.assertRaisesRegexp(ValidationError,
                                    'too long',
                                    self.locations.create_item,
                                    long_path)

    """Path passed to create_location is expected to be saved verbatim."""
    def test_location_path_not_encoded(self):
        self.assertEqual(
            '/foo%20bar', self.locations.create_item('/foo%20bar').path)
        self.assertEqual(
            '/foo~', self.locations.create_item('/foo~').path)
        self.assertEqual(
            '/foo/bar!@7*', self.locations.create_item('/foo/bar!@7*').path)

