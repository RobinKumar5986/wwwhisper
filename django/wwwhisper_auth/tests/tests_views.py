from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from wwwhisper_auth.tests.utils import HttpTestCase

import json
import wwwhisper_auth.models as models

class FakeAssertionVeryfingBackend(ModelBackend):
    def authenticate(self, assertion):
        try:
            return User.objects.get(email=assertion)
        except User.DoesNotExist:
            return None

class AuthTestCase(HttpTestCase):
    def setUp(self):
        self.locations_collection = models.LocationsCollection()
        self.users_collection = models.UsersCollection()

        settings.AUTHENTICATION_BACKENDS = (
            'wwwhisper_auth.tests.FakeAssertionVeryfingBackend',)
        super(AuthTestCase, self).setUp()

class Auth(AuthTestCase):
    def test_is_authorized_requires_path_parameter(self):
        response = self.get('/auth/api/is-authorized/')
        self.assertEqual(400, response.status_code)

    def test_is_authorized_for_not_authenticated_user(self):
        response = self.get('/auth/api/is-authorized/?path=/bar/')
        self.assertEqual(401, response.status_code)

    def test_is_authorized_for_not_authorized_user(self):
        self.users_collection.create_item('foo@example.com')
        self.assertTrue(self.client.login(assertion='foo@example.com'))
        response = self.get('/auth/api/is-authorized/?path=/foo/')
        self.assertEqual(403, response.status_code)

    def test_is_authorized_for_authorized_user(self):
        user = self.users_collection.create_item('foo@example.com')
        location = self.locations_collection.create_item('/foo/')
        location.grant_access(user.uuid)
        self.assertTrue(self.client.login(assertion='foo@example.com'))
        response = self.get('/auth/api/is-authorized/?path=/foo/')
        self.assertEqual(200, response.status_code)

    def test_is_authorized_normalizes_path(self):
        user = self.users_collection.create_item('foo@example.com')
        location = self.locations_collection.create_item('/foo/')
        location.grant_access(user.uuid)
        self.assertTrue(self.client.login(assertion='foo@example.com'))
        response = self.get('/auth/api/is-authorized/?path=/bar/../foo/')
        self.assertEqual(200, response.status_code)

    def test_is_authorized_for_invalid_path(self):
        user = self.users_collection.create_item('foo@example.com')
        self.assertTrue(self.client.login(assertion='foo@example.com'))
        response = self.get('/auth/api/is-authorized/?path=.')
        self.assertEqual(400, response.status_code)


class Login(AuthTestCase):
    def test_login_requires_assertion(self):
        response = self.post('/auth/api/login/', {})
        self.assertEqual(400, response.status_code)

    def test_login_fails_if_unknown_user(self):
        response = self.post('/auth/api/login/',
                             {'assertion' : 'foo@example.com'})
        self.assertEqual(403, response.status_code)

    def test_login_succeeds_if_known_user(self):
        self.users_collection.create_item('foo@example.com')
        response = self.post('/auth/api/login/',
                             {'assertion' : 'foo@example.com'})
        self.assertEqual(200, response.status_code)


class Logout(AuthTestCase):
    def test_authentication_requested_after_logout(self):
        user = self.users_collection.create_item('foo@example.com')
        self.post('/auth/api/login/', {'assertion' : 'foo@example.com'})

        response = self.get('/auth/api/is-authorized/?path=/bar/')
        # Not authorized
        self.assertEqual(403, response.status_code)

        response = self.post('/auth/api/logout/', {})
        self.assertEqual(200, response.status_code)

        response = self.get('/auth/api/is-authorized/?path=/bar/')
        # Not authenticated
        self.assertEqual(401, response.status_code)
