# wwwhisper - web access control.
# Copyright (C) 2016 Jan Wrobel <jan@mixedbit.org>

from django.test import TestCase
from wwwhisper_auth.login_token import generate_login_token
from wwwhisper_auth.login_token import load_login_token

class LoginToken(TestCase):

    def test_load_valid_token(self):
        site_url = 'https://example.org'
        token = generate_login_token(site_url, 'alice@example.org')
        email = load_login_token(site_url, token)
        self.assertEqual('alice@example.org', email)

    def test_load_invalid_token(self):
        site_url = 'https://example.org'
        token = generate_login_token(site_url, 'alice@example.org')
        self.assertIsNone(load_login_token(site_url, token + 'x'))

    def test_load_valid_token_for_different_site(self):
        site_url = 'https://example.org'
        token = generate_login_token(site_url, 'alice@example.org')
        self.assertIsNone(load_login_token('https://foo.org', token))

