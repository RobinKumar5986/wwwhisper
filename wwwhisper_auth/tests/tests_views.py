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

from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from wwwhisper_auth import backend
from wwwhisper_auth import models
from wwwhisper_auth.tests.utils import HttpTestCase

import wwwhisper_auth.urls
import json

INCORRECT_ASSERTION = "ThisAssertionIsFalse"
TEST_SITE = settings.SITE_URL

class FakeAssertionVeryfingBackend(ModelBackend):
    def __init__(self):
        self.users = models.UsersCollection()

    def authenticate(self, assertion, site_id=TEST_SITE, site_url=TEST_SITE):
        if assertion == INCORRECT_ASSERTION:
            raise backend.AssertionVerificationException(
                'Assertion verification failed.')
        return self.users.find_item_by_email(site_id, assertion)

class AuthTestCase(HttpTestCase):
    def setUp(self):
        self.locations = models.LocationsCollection()
        self.users = models.UsersCollection()
        models.create_site(TEST_SITE)

        settings.AUTHENTICATION_BACKENDS = (
            'wwwhisper_auth.tests.FakeAssertionVeryfingBackend',)
        super(AuthTestCase, self).setUp()

class AuthTest(AuthTestCase):
    def test_is_authorized_requires_path_parameter(self):
        response = self.get('/auth/api/is-authorized/?pat=/foo')
        self.assertEqual(400, response.status_code)

    def test_is_authorized_for_not_authenticated_user(self):
        location = self.locations.create_item(TEST_SITE, '/foo/')
        response = self.get('/auth/api/is-authorized/?path=/foo/')
        self.assertEqual(401, response.status_code)
        self.assertTrue(response.has_header('WWW-Authenticate'))
        self.assertFalse(response.has_header('User'))
        self.assertEqual('VerifiedEmail', response['WWW-Authenticate'])
        self.assertRegexpMatches(response['Content-Type'], "text/plain")
        self.assertEqual('Authentication required.', response.content)

    def test_is_authorized_for_not_authorized_user(self):
        self.users.create_item(TEST_SITE, 'foo@example.com')
        self.assertTrue(self.client.login(assertion='foo@example.com'))
        response = self.get('/auth/api/is-authorized/?path=/foo/')
        # For an authenticated user 'User' header should be always returned.
        self.assertEqual('foo@example.com', response['User'])
        self.assertEqual(403, response.status_code)
        self.assertRegexpMatches(response['Content-Type'], "text/plain")
        self.assertEqual('User not authorized.', response.content)

    def test_is_authorized_for_authorized_user(self):
        user = self.users.create_item(TEST_SITE, 'foo@example.com')
        location = self.locations.create_item(TEST_SITE, '/foo/')
        location.grant_access(user.uuid)
        self.assertTrue(self.client.login(assertion='foo@example.com'))
        response = self.get('/auth/api/is-authorized/?path=/foo/')
        self.assertEqual('foo@example.com', response['User'])
        self.assertEqual(200, response.status_code)

    def test_is_authorized_for_user_of_other_site(self):
        site2_id = 'somesite'
        models.create_site(site2_id)
        user = self.users.create_item(site2_id, 'foo@example.com')
        location = self.locations.create_item(TEST_SITE, '/foo/')
        self.assertTrue(self.client.login(
                assertion='foo@example.com', site_id=site2_id))
        response = self.get('/auth/api/is-authorized/?path=/foo/')

    def test_is_authorized_for_open_location(self):
        location = self.locations.create_item(TEST_SITE, '/foo/')
        location.grant_open_access(require_login=False)
        response = self.get('/auth/api/is-authorized/?path=/foo/')
        self.assertFalse(response.has_header('User'))
        self.assertEqual(200, response.status_code)

    def test_is_authorized_for_open_location_and_authenticated_user(self):
        user = self.users.create_item(TEST_SITE, 'foo@example.com')
        self.assertTrue(self.client.login(assertion='foo@example.com'))
        location = self.locations.create_item(TEST_SITE, '/foo/')
        location.grant_open_access(require_login=False)
        response = self.get('/auth/api/is-authorized/?path=/foo/')
        self.assertEqual('foo@example.com', response['User'])
        self.assertEqual(200, response.status_code)

    def test_is_authorized_for_invalid_path(self):
        user = self.users.create_item(TEST_SITE, 'foo@example.com')
        location = self.locations.create_item(TEST_SITE, '/foo/')
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
        location = self.locations.create_item(TEST_SITE, '/f/')
        location.grant_open_access(require_login=False)
        response = self.get('/auth/api/is-authorized/?path=%2F%66%2F')
        self.assertEqual(200, response.status_code)

        response = self.get('/auth/api/is-authorized/?path=%2F%66')
        self.assertEqual(401, response.status_code)

    def test_is_authorized_collapses_slashes(self):
        location = self.locations.create_item(TEST_SITE, '/f/')
        location.grant_open_access(require_login=False)
        response = self.get('/auth/api/is-authorized/?path=///f/')
        self.assertEqual(200, response.status_code)

    def test_is_authorized_does_not_allow_requests_with_user_header(self):
        user = self.users.create_item(TEST_SITE, 'foo@example.com')
        location = self.locations.create_item(TEST_SITE, '/foo/')
        location.grant_access(user.uuid)
        self.assertTrue(self.client.login(assertion='foo@example.com'))
        response = self.client.get('/auth/api/is-authorized/?path=/foo/',
                                   HTTP_USER='bar@example.com')
        self.assertEqual(400, response.status_code)

    def test_caching_disabled_for_auth_request_results(self):
        response = self.get('/auth/api/is-authorized/?path=/foo/')
        self.assertTrue(response.has_header('Cache-Control'))
        control = response['Cache-Control']
        # index throws ValueError if not found.
        control.index('no-cache')
        control.index('no-store')
        control.index('must-revalidate')
        control.index('max-age=0')

class AuthStaticAssetsTest(AuthTestCase):
    def setUp(self):
        settings.WWWHISPER_STATIC = './www_static'
        reload(wwwhisper_auth.urls)
        super(AuthStaticAssetsTest, self).setUp()

    def tearDown(self):
        settings.WWWHISPER_STATIC = None
        reload(wwwhisper_auth.urls)

    def test_is_authorized_for_not_authenticated_user(self):
        location = self.locations.create_item(TEST_SITE, '/foo/')
        response = self.client.get('/auth/api/is-authorized/?path=/foo/',
                                   HTTP_ACCEPT='text/plain, text/html')
        self.assertEqual(401, response.status_code)
        self.assertRegexpMatches(response['Content-Type'], 'text/html')
        self.assertRegexpMatches(response.content, '<body')

        response = self.client.get('/auth/api/is-authorized/?path=/foo/',
                                   HTTP_ACCEPT='text/plain')
        self.assertEqual(401, response.status_code)
        self.assertRegexpMatches(response['Content-Type'], 'text/plain')

    def test_html_response_is_authorized_for_not_authorized_user(self):
        self.users.create_item(TEST_SITE, 'foo@example.com')
        self.assertTrue(self.client.login(assertion='foo@example.com'))
        response = self.client.get('/auth/api/is-authorized/?path=/foo/',
                                   HTTP_ACCEPT='*/*')
        self.assertEqual(403, response.status_code)
        self.assertRegexpMatches(response['Content-Type'], 'text/html')
        self.assertRegexpMatches(response.content, '<body')

        response = self.client.get('/auth/api/is-authorized/?path=/foo/',
                                   HTTP_ACCEPT='text/plain, audio/*')
        self.assertEqual(403, response.status_code)
        self.assertRegexpMatches(response['Content-Type'], 'text/plain')


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
        self.users.create_item(TEST_SITE, 'foo@example.com')
        response = self.post('/auth/api/login/',
                             {'assertion' : 'foo@example.com'})
        self.assertEqual(204, response.status_code)


class LogoutTest(AuthTestCase):
    def test_authentication_requested_after_logout(self):
        user = self.users.create_item(TEST_SITE, 'foo@example.com')
        self.post('/auth/api/login/', {'assertion' : 'foo@example.com'})

        response = self.get('/auth/api/is-authorized/?path=/bar/')
        # Not authorized
        self.assertEqual(403, response.status_code)

        response = self.post('/auth/api/logout/', {})
        self.assertEqual(204, response.status_code)

        response = self.get('/auth/api/is-authorized/?path=/bar/')
        # Not authenticated
        self.assertEqual(401, response.status_code)


class WhoAmITest(AuthTestCase):
    def test_whoami_returns_email_of_logged_in_user(self):
        self.users.create_item(TEST_SITE, 'foo@example.com')

        # Not authorized.
        response = self.get('/auth/api/whoami/')
        self.assertEqual(401, response.status_code)

        self.post('/auth/api/login/', {'assertion' : 'foo@example.com'})

        response = self.get('/auth/api/whoami/')
        self.assertEqual(200, response.status_code)
        parsed_response_body = json.loads(response.content)
        self.assertEqual('foo@example.com', parsed_response_body['email'])

    def test_whoami_for_user_of_differen_site(self):
        site2_id = 'somesite'
        models.create_site(site2_id)
        self.users.create_item(site2_id, 'foo@example.com')
        self.assertTrue(self.client.login(
                assertion='foo@example.com', site_id=site2_id))
        # Not authorized.
        # Request is run for TEST_SITE, but user belongs to site2_id.
        response = self.get('/auth/api/whoami/')
        self.assertEqual(401, response.status_code)

class CsrfTokenTest(AuthTestCase):

    def test_token_in_body_matches_cookie(self):
        response = self.post('/auth/api/csrftoken/', {})
        self.assertEqual(200, response.status_code)
        parsed_response_body = json.loads(response.content)
        self.assertTrue(len(parsed_response_body['csrfToken']) > 20)
        self.assertEqual(
            response.cookies[settings.CSRF_COOKIE_NAME].coded_value,
            parsed_response_body['csrfToken'])

    # Ensures that ProtectCookiesMiddleware is applied.
    def test_csrf_cookie_http_only(self):
        response = self.post('/auth/api/csrftoken/', {})
        self.assertTrue(response.cookies[settings.CSRF_COOKIE_NAME]['httponly'])
