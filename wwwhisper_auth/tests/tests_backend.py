# wwwhisper - web access control.
# Copyright (C) 2016 Jan Wrobel <jan@mixedbit.org>

from django.test import TestCase

from wwwhisper_auth.backend import AuthenticationError, VerifiedEmailBackend
from wwwhisper_auth.models import SitesCollection

TEST_SITE_URL = 'https://example.com'
TEST_USER_EMAIL = 'foo@example.com'

class VerifiedEmailBackendTest(TestCase):

    def setUp(self):
        self.sites = SitesCollection()
        self.backend = VerifiedEmailBackend()

    def test_authentication_valid(self):
        site = self.sites.create_item(TEST_SITE_URL)
        user = site.users.create_item(TEST_USER_EMAIL)
        auth_user = self.backend.authenticate(
            site, TEST_SITE_URL, TEST_USER_EMAIL)
        self.assertEqual(user, auth_user)

    def test_no_such_user(self):
        site = self.sites.create_item(TEST_SITE_URL)
        auth_user = self.backend.authenticate(
            site, TEST_SITE_URL, TEST_USER_EMAIL)
        self.assertIsNone(auth_user)

    def test_site_with_open_location_user_created(self):
        site = self.sites.create_item(TEST_SITE_URL)
        location = site.locations.create_item('/foo/')
        location.grant_open_access(require_login=True)
        auth_user = self.backend.authenticate(
            site, TEST_SITE_URL, TEST_USER_EMAIL)
        self.assertIsNotNone(auth_user)
        self.assertEqual(TEST_USER_EMAIL, auth_user.email)


    def test_site_with_open_location_user_limit_exceeded(self):
        site = self.sites.create_item(TEST_SITE_URL)
        site.users_limit = 0
        location = site.locations.create_item('/foo/')
        location.grant_open_access(require_login=True)
        self.assertRaisesRegexp(AuthenticationError,
                                'Users limit exceeded',
                                self.backend.authenticate,
                                site,
                                TEST_SITE_URL,
                                TEST_USER_EMAIL)
