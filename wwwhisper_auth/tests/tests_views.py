# wwwhisper - web access control.
# Copyright (C) 2012-2015 Jan Wrobel <jan@mixedbit.org>

from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from wwwhisper_auth import backend
from wwwhisper_auth.tests.utils import HttpTestCase
from wwwhisper_auth.tests.utils import TEST_SITE

import json
import wwwhisper_auth.urls

INCORRECT_ASSERTION = "ThisAssertionIsFalse"

class FakeAssertionVeryfingBackend(ModelBackend):
    def authenticate(self, assertion, site, site_url=TEST_SITE):
        if assertion == INCORRECT_ASSERTION:
            raise backend.AssertionVerificationException(
                'Assertion verification failed.')
        return site.users.find_item_by_email(assertion)

class AuthTestCase(HttpTestCase):
    def setUp(self):
        settings.AUTHENTICATION_BACKENDS = (
            'wwwhisper_auth.tests.FakeAssertionVeryfingBackend',)
        super(AuthTestCase, self).setUp()

    def login(self, email, site=None):
        if site is None:
            site = self.site
        self.assertTrue(self.client.login(assertion=email, site=site))
        # Login needs to set user_id in session.
        user = site.users.find_item_by_email(email)
        self.assertIsNotNone(user)
        # Session must be stored in a temporary variable, otherwise
        # updating does not work.
        s = self.client.session
        s['user_id'] = user.id
        s.save()

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
        self.site.users.create_item('foo@example.com')
        response = self.post('/auth/api/login/',
                             {'assertion' : 'foo@example.com'})
        self.assertEqual(204, response.status_code)

class AuthTest(AuthTestCase):
    def test_is_authorized_requires_path_parameter(self):
        response = self.get('/auth/api/is-authorized/?pat=/foo')
        self.assertEqual(400, response.status_code)

    def test_is_authorized_if_not_authenticated(self):
        location = self.site.locations.create_item('/foo/')
        response = self.get('/auth/api/is-authorized/?path=/foo/')
        self.assertEqual(401, response.status_code)
        self.assertTrue(response.has_header('WWW-Authenticate'))
        self.assertFalse(response.has_header('User'))
        self.assertEqual('VerifiedEmail', response['WWW-Authenticate'])
        self.assertRegexpMatches(response['Content-Type'], "text/plain")
        self.assertEqual('Authentication required.', response.content)

    def test_is_authorized_if_not_authorized(self):
        self.site.users.create_item('foo@example.com')
        self.login('foo@example.com')
        response = self.get('/auth/api/is-authorized/?path=/foo/')
        # For an authenticated user 'User' header should be always returned.
        self.assertEqual(403, response.status_code)
        self.assertEqual('foo@example.com', response['User'])
        self.assertRegexpMatches(response['Content-Type'], "text/plain")
        self.assertEqual('User not authorized.', response.content)

    def test_is_authorized_if_authorized(self):
        user = self.site.users.create_item('foo@example.com')
        location = self.site.locations.create_item('/foo/')
        location.grant_access(user.uuid)
        self.login('foo@example.com')
        response = self.get('/auth/api/is-authorized/?path=/foo/')
        self.assertEqual(200, response.status_code)
        self.assertEqual('foo@example.com', response['User'])

    def test_is_authorized_if_user_of_other_site(self):
        site2 = self.sites.create_item('somesite')
        user = site2.users.create_item('foo@example.com')
        location = self.site.locations.create_item('/foo/')
        self.login('foo@example.com', site2)
        response = self.get('/auth/api/is-authorized/?path=/foo/')

    def test_is_authorized_if_open_location(self):
        location = self.site.locations.create_item('/foo/')
        location.grant_open_access(require_login=False)
        response = self.get('/auth/api/is-authorized/?path=/foo/')
        self.assertFalse(response.has_header('User'))
        self.assertEqual(200, response.status_code)

    def test_is_authorized_if_open_location_and_authenticated(self):
        user = self.site.users.create_item('foo@example.com')
        self.login('foo@example.com')
        location = self.site.locations.create_item('/foo/')
        location.grant_open_access(require_login=False)
        response = self.get('/auth/api/is-authorized/?path=/foo/')
        self.assertEqual(200, response.status_code)
        self.assertEqual('foo@example.com', response['User'])

    def test_is_authorized_if_invalid_path(self):
        user = self.site.users.create_item('foo@example.com')
        location = self.site.locations.create_item('/foo/')
        location.grant_access(user.uuid)
        self.login('foo@example.com')

        response = self.get('/auth/api/is-authorized/?path=/bar/../foo/')
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(response.content,
                                 'Path should be absolute and normalized')

        response = self.get('/auth/api/is-authorized/?path=.')
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(response.content,
                                 'Path should be absolute and normalized')

    def test_is_authorized_decodes_path(self):
        location = self.site.locations.create_item('/f/')
        location.grant_open_access(require_login=False)
        response = self.get('/auth/api/is-authorized/?path=%2F%66%2F')
        self.assertEqual(200, response.status_code)

        response = self.get('/auth/api/is-authorized/?path=%2F%66')
        self.assertEqual(401, response.status_code)

    def test_is_authorized_collapses_slashes(self):
        location = self.site.locations.create_item('/f/')
        location.grant_open_access(require_login=False)
        response = self.get('/auth/api/is-authorized/?path=///f/')
        self.assertEqual(200, response.status_code)

    def test_is_authorized_does_not_allow_requests_with_user_header(self):
        user = self.site.users.create_item('foo@example.com')
        location = self.site.locations.create_item('/foo/')
        location.grant_access(user.uuid)
        self.login('foo@example.com')
        response = self.get('/auth/api/is-authorized/?path=/foo/',
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

    # Make sure HTML responses are returned when request accepts HTML.

    def test_is_authorized_if_not_authenticated_html_response(self):
        location = self.site.locations.create_item('/foo/')
        response = self.get('/auth/api/is-authorized/?path=/foo/',
                            HTTP_ACCEPT='text/plain, text/html')
        self.assertEqual(401, response.status_code)
        self.assertRegexpMatches(response['Content-Type'], 'text/html')
        self.assertRegexpMatches(response.content, '<body')

        response = self.get('/auth/api/is-authorized/?path=/foo/',
                            HTTP_ACCEPT='text/plain')
        self.assertEqual(401, response.status_code)
        self.assertRegexpMatches(response['Content-Type'], 'text/plain')

    def test_is_authorized_if_not_authenticated_custom_html_response(self):
        self.site.update_skin(
            title='Foo', header='Bar', message='Baz', branding=False)
        response = self.get('/auth/api/is-authorized/?path=/foo/',
                            HTTP_ACCEPT='*/*')
        self.assertEqual(401, response.status_code)
        self.assertRegexpMatches(response['Content-Type'], 'text/html')
        self.assertRegexpMatches(response.content, '<title>Foo</title>')
        self.assertRegexpMatches(response.content, '<h1>Bar</h1>')
        self.assertRegexpMatches(response.content, 'class="lead">Baz')

    def test_is_authorized_if_not_authorized_html_response(self):
        self.site.users.create_item('foo@example.com')
        self.login('foo@example.com')
        response = self.get('/auth/api/is-authorized/?path=/foo/',
                            HTTP_ACCEPT='*/*')
        self.assertEqual(403, response.status_code)
        self.assertRegexpMatches(response['Content-Type'], 'text/html')
        self.assertRegexpMatches(response.content, '<body')

        response = self.get('/auth/api/is-authorized/?path=/foo/',
                            HTTP_ACCEPT='text/plain, audio/*')
        self.assertEqual(403, response.status_code)
        self.assertRegexpMatches(response['Content-Type'], 'text/plain')

class LogoutTest(AuthTestCase):
    def test_authentication_requested_after_logout(self):
        user = self.site.users.create_item('foo@example.com')
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
        self.site.users.create_item('foo@example.com')

        # Not authorized.
        response = self.get('/auth/api/whoami/')
        self.assertEqual(401, response.status_code)

        self.post('/auth/api/login/', {'assertion' : 'foo@example.com'})
        response = self.get('/auth/api/whoami/')
        self.assertEqual(200, response.status_code)
        parsed_response_body = json.loads(response.content)
        self.assertEqual('foo@example.com', parsed_response_body['email'])

    def test_whoami_for_user_of_differen_site(self):
        site2 = self.sites.create_item('somesite')
        site2.users.create_item('foo@example.com')
        self.login('foo@example.com', site2)
        # Not authorized.
        # Request is run for TEST_SITE, but user belongs to site2_id.
        response = self.get('/auth/api/whoami/')
        self.assertEqual(401, response.status_code)

class CsrfTokenTest(AuthTestCase):

    def test_token_returned_in_cookie(self):
        response = self.get('/auth/api/csrftoken/')
        self.assertEqual(204, response.status_code)
        self.assertTrue(
            len(response.cookies[settings.CSRF_COOKIE_NAME].coded_value) > 20)

    # Ensures that ProtectCookiesMiddleware is applied.
    def test_csrf_cookie_http_only(self):
        response = self.get('/auth/api/csrftoken/')
        self.assertTrue(response.cookies[settings.CSRF_COOKIE_NAME]['secure'])


class SessionCacheTest(AuthTestCase):
    def test_user_cached_in_session(self):
        user = self.site.users.create_item('foo@example.com')
        response = self.post('/auth/api/login/',
                             {'assertion' : 'foo@example.com'})
        self.assertEqual(204, response.status_code)
        s = self.client.session
        user_id = s['user_id']
        self.assertIsNotNone(user_id)
        self.assertEqual(user_id, user.id)
