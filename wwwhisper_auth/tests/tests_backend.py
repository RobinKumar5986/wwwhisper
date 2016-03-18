# wwwhisper - web access control.
# Copyright (C) 2016 Jan Wrobel <jan@mixedbit.org>

from django.test import TestCase

from wwwhisper_auth.backend import AuthenticationError, TokenBackend
from wwwhisper_auth.models import SitesCollection

TEST_SITE_URL = 'https://example.com'
TEST_USER_EMAIL = 'foo@example.com'

class TokenBackendTest(TestCase):

    def setUp(self):
        self.sites = SitesCollection()
        self.backend = TokenBackend()

    def test_authentication_valid(self):
        site = self.sites.create_item(TEST_SITE_URL)
        user = site.users.create_item(TEST_USER_EMAIL)
        token_data = {
            'email': TEST_USER_EMAIL,
            'site_url': TEST_SITE_URL
        }
        auth_user = self.backend.authenticate(site, TEST_SITE_URL, token_data)
        self.assertEqual(user, auth_user)

    def test_no_such_user(self):
        site = self.sites.create_item(TEST_SITE_URL)
        token_data = {
            'email': TEST_USER_EMAIL,
            'site_url': TEST_SITE_URL
        }
        auth_user = self.backend.authenticate(site, TEST_SITE_URL, token_data)
        self.assertIsNone(auth_user)

    def test_token_for_different_sie(self):
        site = self.sites.create_item(TEST_SITE_URL)
        token_data = {
            'email': TEST_USER_EMAIL,
            'site_url': TEST_SITE_URL + '.uk'
        }
        self.assertRaisesRegexp(AuthenticationError,
                                'Invalid token.',
                                self.backend.authenticate,
                                site,
                                TEST_SITE_URL,
                                token_data)

    def test_site_with_open_location_user_created(self):
        site = self.sites.create_item(TEST_SITE_URL)
        location = site.locations.create_item('/foo/')
        location.grant_open_access(require_login=True)
        token_data = {
            'email': TEST_USER_EMAIL,
            'site_url': TEST_SITE_URL
        }
        auth_user = self.backend.authenticate(site, TEST_SITE_URL, token_data)
        self.assertIsNotNone(auth_user)
        self.assertEqual(TEST_USER_EMAIL, auth_user.email)


    def test_site_with_open_location_user_limit_exceeded(self):
        site = self.sites.create_item(TEST_SITE_URL)
        site.users_limit = 0
        location = site.locations.create_item('/foo/')
        location.grant_open_access(require_login=True)
        token_data = {
            'email': TEST_USER_EMAIL,
            'site_url': TEST_SITE_URL
        }
        self.assertRaisesRegexp(AuthenticationError,
                                'Users limit exceeded',
                                self.backend.authenticate,
                                site,
                                TEST_SITE_URL,
                                token_data)
