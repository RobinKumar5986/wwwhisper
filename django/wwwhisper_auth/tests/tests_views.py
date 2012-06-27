from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from wwwhisper_auth import backend
from wwwhisper_auth import models
from wwwhisper_auth.tests.utils import HttpTestCase

import json

INCORRECT_ASSERTION="ThisAssertionIsFalse"

class FakeAssertionVeryfingBackend(ModelBackend):
    def authenticate(self, assertion):
        try:
            if assertion == INCORRECT_ASSERTION:
                raise backend.AssertionVerificationException(
                    'Assertion verification failed.')
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

class AuthTest(AuthTestCase):
    def test_is_authorized_requires_path_parameter(self):
        response = self.get('/auth/api/is-authorized/?pat=/foo')
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

    def test_is_authorized_for_open_location(self):
        location = self.locations_collection.create_item('/foo/')
        location.grant_open_access()
        response = self.get('/auth/api/is-authorized/?path=/foo/')
        self.assertEqual(200, response.status_code)

    def test_is_authorized_for_open_location_and_authenticated_user(self):
        user = self.users_collection.create_item('foo@example.com')
        self.assertTrue(self.client.login(assertion='foo@example.com'))
        location = self.locations_collection.create_item('/foo/')
        location.grant_open_access()
        response = self.get('/auth/api/is-authorized/?path=/foo/')
        self.assertEqual(200, response.status_code)

    def test_is_authorized_for_invalid_path(self):
        user = self.users_collection.create_item('foo@example.com')
        location = self.locations_collection.create_item('/foo/')
        location.grant_access(user.uuid)
        self.assertTrue(self.client.login(assertion='foo@example.com'))

        response = self.get('/auth/api/is-authorized/?path=/bar/../foo/')
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(response.content,
                                 'Path should be absolute and normalized')

        response = self.get('/auth/api/is-authorized/?path=.')
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(response.content,
                                 'Path should be absolute and normalized')

    def test_is_authorized_decodes_path(self):
        location = self.locations_collection.create_item('/f/')
        location.grant_open_access()
        response = self.get('/auth/api/is-authorized/?path=%2F%66%2F')
        self.assertEqual(200, response.status_code)

        response = self.get('/auth/api/is-authorized/?path=%2F%66')
        self.assertEqual(401, response.status_code)

class LoginTest(AuthTestCase):
    def test_login_requires_assertion(self):
        response = self.post('/auth/api/login/', {})
        self.assertEqual(400, response.status_code)

    def test_login_fails_if_unknown_user(self):
        response = self.post('/auth/api/login/',
                             {'assertion' : 'foo@example.com'})
        self.assertEqual(403, response.status_code)

    def test_login_fails_if_incorrect_assertion(self):
        response = self.post('/auth/api/login/',
                             {'assertion' : INCORRECT_ASSERTION})
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(
            response.content, 'Assertion verification failed')

    def test_login_succeeds_if_known_user(self):
        self.users_collection.create_item('foo@example.com')
        response = self.post('/auth/api/login/',
                             {'assertion' : 'foo@example.com'})
        self.assertEqual(204, response.status_code)


class LogoutTest(AuthTestCase):
    def test_authentication_requested_after_logout(self):
        user = self.users_collection.create_item('foo@example.com')
        self.post('/auth/api/login/', {'assertion' : 'foo@example.com'})

        response = self.get('/auth/api/is-authorized/?path=/bar/')
        # Not authorized
        self.assertEqual(403, response.status_code)

        response = self.post('/auth/api/logout/', {})
        self.assertEqual(204, response.status_code)

        response = self.get('/auth/api/is-authorized/?path=/bar/')
        # Not authenticated
        self.assertEqual(401, response.status_code)
