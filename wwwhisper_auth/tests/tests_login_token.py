# wwwhisper - web access control.
# Copyright (C) 2016 Jan Wrobel <jan@mixedbit.org>

from django.test import TestCase
from wwwhisper_auth.login_token import generate_login_token
from wwwhisper_auth.login_token import load_login_token
from wwwhisper_auth.models import SitesCollection
from wwwhisper_auth.models import SINGLE_SITE_ID

TEST_SITE = 'https://foo.example.org:8080'

class LoginToken(TestCase):

    def setUp(self):
        self.sites = SitesCollection()
        # For each test case, test site must exist, so it can be set
        # by SetSiteMiddleware
        self.site = self.sites.create_item(SINGLE_SITE_ID)
        self.site.aliases.create_item(TEST_SITE)

    def test_load_valid_token(self):
        token = generate_login_token(self.site, TEST_SITE, 'alice@example.org')
        email = load_login_token(self.site, TEST_SITE, token)
        self.assertEqual('alice@example.org', email)

    def test_load_invalid_token(self):
        token = generate_login_token(self.site, TEST_SITE, 'alice@example.org')
        self.assertIsNone(load_login_token(self.site, TEST_SITE, token + 'x'))

    def test_load_valid_token_for_different_site(self):
        token = generate_login_token(self.site, TEST_SITE, 'alice@example.org')
        self.assertIsNone(load_login_token(self.site, 'https://foo.org', token))

