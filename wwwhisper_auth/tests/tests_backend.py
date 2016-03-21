# wwwhisper - web access control.
# Copyright (C) 2016 Jan Wrobel <jan@mixedbit.org>

from django.test import TestCase

from wwwhisper_auth.backend import AuthenticationError, VerifiedEmailBackend
from wwwhisper_auth.login_token import generate_login_token
from wwwhisper_auth.models import SitesCollection

TEST_SITE_URL = 'https://example.com'
TEST_USER_EMAIL = 'foo@example.com'

class VerifiedEmailBackendTest(TestCase):

    def setUp(self):
        self.sites = SitesCollection()
        self.backend = VerifiedEmailBackend()

    def user_token(self):
        return generate_login_token(TEST_SITE_URL, TEST_USER_EMAIL)

    def test_token_valid(self):
        site = self.sites.create_item(TEST_SITE_URL)
        user = site.users.create_item(TEST_USER_EMAIL)
        auth_user = self.backend.authenticate(
            site, TEST_SITE_URL, self.user_token())
        self.assertEqual(user, auth_user)

    def test_token_invalid(self):
        site = self.sites.create_item(TEST_SITE_URL)
        user = site.users.create_item(TEST_USER_EMAIL)
        self.assertRaisesRegexp(AuthenticationError,
                                'Token invalid or expired',
                                self.backend.authenticate,
                                site,
                                TEST_SITE_URL,
                                self.user_token() + 'x')

    def test_token_for_different_site(self):
        site = self.sites.create_item(TEST_SITE_URL)
        user = site.users.create_item(TEST_USER_EMAIL)
        token = generate_login_token('http://example.com', TEST_USER_EMAIL)
        self.assertRaisesRegexp(AuthenticationError,
                                'Token invalid or expired',
                                self.backend.authenticate,
                                site,
                                TEST_SITE_URL,
                                token)

    def test_no_such_user(self):
        site = self.sites.create_item(TEST_SITE_URL)
        auth_user = self.backend.authenticate(
            site, TEST_SITE_URL, self.user_token())
        self.assertIsNone(auth_user)

    def test_site_with_open_location_user_created(self):
        site = self.sites.create_item(TEST_SITE_URL)
        location = site.locations.create_item('/foo/')
        location.grant_open_access(require_login=True)
        auth_user = self.backend.authenticate(
            site, TEST_SITE_URL, self.user_token())
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
                                self.user_token())
