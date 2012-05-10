from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from django.conf import settings
from django.contrib.auth.backends import ModelBackend

import json
import wwwhisper_auth.acl as acl


class FakeAssertionVeryfingBackend(ModelBackend):
    def authenticate(self, assertion, audience = None):
        try:
            return User.objects.get(username=assertion)
        except User.DoesNotExist:
            return None

class AuthTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        settings.AUTHENTICATION_BACKENDS = (
            'wwwhisper_auth.tests.FakeAssertionVeryfingBackend',)

    def json_post(self, path, args):
        return self.client.post(path,
                                json.dumps(args),
                                'text/json',
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

class Auth(AuthTestCase):
    def test_is_authorized_requires_path_parameter(self):
        response = self.client.get('/auth/api/is_authorized/')
        self.assertEqual(400, response.status_code)

    def test_is_authorized_for_not_authenticated_user(self):
        response = self.client.get('/auth/api/is_authorized/?path=/bar/')
        self.assertEqual(403, response.status_code)

    def test_is_authorized_for_not_authorized_user(self):
        self.assertTrue(acl.add_user('foo@example.com'))
        self.assertTrue(self.client.login(assertion='foo@example.com'))
        response = self.client.get('/auth/api/is_authorized/?path=/foo/')
        self.assertEqual(401, response.status_code)

    def test_is_authorized_for_authorized_user(self):
        self.assertTrue(acl.add_user('foo@example.com'))
        self.assertTrue(acl.add_location('/foo/'))
        self.assertTrue(acl.grant_access('foo@example.com', '/foo/'))
        self.assertTrue(self.client.login(assertion='foo@example.com'))
        response = self.client.get('/auth/api/is_authorized/?path=/foo/')
        self.assertEqual(200, response.status_code)


class Login(AuthTestCase):
    def test_login_requires_assertion(self):
        response = self.client.post('/auth/api/login/', {})
        self.assertEqual(400, response.status_code)

    def test_login_fails_if_unknown_user(self):
        response = self.json_post('/auth/api/login/',
                                  {'assertion' : 'foo@example.com'})
        self.assertEqual(400, response.status_code)

    def test_login_succeeds_if_known_user(self):
        acl.add_user('foo@example.com')
        response = self.json_post('/auth/api/login/',
                                  {'assertion' : 'foo@example.com'})
        self.assertEqual(200, response.status_code)


class Logout(AuthTestCase):
    def test_authentication_requested_after_logout(self):
        acl.add_user('foo@example.com')
        self.json_post('/auth/api/login/', {'assertion' : 'foo@example.com'})

        response = self.client.get('/auth/api/is_authorized/?path=/bar/')
        # Not authorized
        self.assertEqual(401, response.status_code)

        response = self.client.post('/auth/api/logout/')
        self.assertEqual(200, response.status_code)

        response = self.client.get('/auth/api/is_authorized/?path=/bar/')
        # Not authenticated
        self.assertEqual(403, response.status_code)
