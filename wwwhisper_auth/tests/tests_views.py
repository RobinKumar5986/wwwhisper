# wwwhisper - web access control.
# Copyright (C) 2012-2016 Jan Wrobel <jan@mixedbit.org>


from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.core import mail

from wwwhisper_auth.login_token import generate_login_token
from wwwhisper_auth.tests.utils import HttpTestCase
from wwwhisper_auth.tests.utils import TEST_SITE

import wwwhisper_auth.urls

import json
import urllib

class AuthTestCase(HttpTestCase):
    def setUp(self):
       settings.EMAIL_BACKEND = \
            'django.core.mail.backends.locmem.EmailBackend'
        settings.TOKEN_EMAIL_FROM = 'verify@wwwhisper.io'
        super(AuthTestCase, self).setUp()

    def tearDown(self):
        if mail.outbox:
           mail.outbox = []

    def login(self, email, site=None):
        if site is None:
            site = self.site
        token = generate_login_token(site, TEST_SITE, email)
        self.assertTrue(self.client.login(site=site, site_url=TEST_SITE, token=token))
        # Login needs to set user_id in session.
        user = site.users.find_item_by_email(email)
        self.assertIsNotNone(user)
        # Session must be stored in a temporary variable, otherwise
        # updating does not work.
        s = self.client.session
        s['user_id'] = user.id
        s.save()

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
        self.assertEqual(401, response.status_code)

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
        self.login('foo@example.com')

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

        self.login('foo@example.com')
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

class SendTokenTest(AuthTestCase):
    def test_email_send(self):
        response = self.post('/auth/api/send-token/',
                             {'email': 'alice@example.org', 'path': '/foo/bar'})
        self.assertEqual(204, response.status_code)
        self.assertEqual(1, len(mail.outbox))
        msg = mail.outbox[0]
        self.assertEqual('[{0}] email verification'.format(TEST_SITE),
                         msg.subject)
        self.assertEqual(1, len(msg.to))
        self.assertEqual('verify@wwwhisper.io', msg.from_email)
        self.assertEqual('alice@example.org', msg.to[0])
        path = urllib.urlencode({'next': '/foo/bar'})
        regexp = (TEST_SITE + '/auth/api/login/\?token=.{60,}&' + path +
                  '\n')
        self.assertRegexpMatches(msg.body, regexp)

    def test_email_address_is_none(self):
        response = self.post('/auth/api/send-token/',
                             {'email': None, 'path': '/'})
        self.assertEqual(400, response.status_code)
        self.assertEqual('Email not set.', response.content)

    def test_email_has_invalid_format(self):
        response = self.post('/auth/api/send-token/',
                             {'email': 'alice', 'path': '/'})
        self.assertEqual(400, response.status_code)
        self.assertEqual('Email has invalid format.', response.content)

    def test_tricky_redirection_replaced(self):
        response = self.post('/auth/api/send-token/',
                             {'email': 'alice@example.org', 'path': '/foo/../'})
        self.assertEqual(204, response.status_code)
        msg = mail.outbox[0]
        # Login ignores '/foo/../' and redirects to '/'.
        path = urllib.urlencode({'next': '/'})
        regexp = (TEST_SITE + '/auth/api/login/\?token=.{60,}&' + path +
                  '\n')
        self.assertRegexpMatches(msg.body, regexp)

class LoginTest(AuthTestCase):
    def setUp(self):
        super(AuthTestCase, self).setUp()

    def test_login_fails_if_token_missing(self):
        response = self.get('/auth/api/login/')
        self.assertEqual(400, response.status_code)
        self.assertEqual('Token missing.', response.content)

    def test_login_fails_if_token_invalid(self):
        response = self.get('/auth/api/login/?token=xyz')
        self.assertEqual(400, response.status_code)
        self.assertEqual('Token invalid or expired.', response.content)

    def test_login_fails_if_token_for_different_site_url(self):
        self.site.users.create_item('foo@example.org')
        token = generate_login_token(
            self.site, 'https://foo.com', 'foo@example.org')
        response = self.get('/auth/api/login/?token=' + token)
        self.assertEqual(400, response.status_code)
        self.assertEqual('Token invalid or expired.', response.content)

    def test_login_succeeds_if_known_user(self):
        self.site.users.create_item('foo@example.org')
        token = generate_login_token(self.site, TEST_SITE, 'foo@example.org')
        params = urllib.urlencode(dict(token=token, next='/foo'))
        response = self.get('/auth/api/login/?' + params)
        self.assertEqual(302, response.status_code)
        self.assertEqual(TEST_SITE + '/foo', response['Location'])

    def test_login_fails_if_unknown_user(self):
        token = generate_login_token(self.site, TEST_SITE, 'foo@example.org')
        response = self.get('/auth/api/login/?token=' + token)
        self.assertEqual(403, response.status_code)

    def test_login_succeeds_if_unknown_user_but_site_has_open_locations(self):
        location = self.site.locations.create_item('/foo/')
        location.grant_open_access(require_login=True)
        token = generate_login_token(self.site, TEST_SITE, 'foo@example.org')
        params = urllib.urlencode(dict(token=token, next='/foo'))
        response = self.get('/auth/api/login/?' + params)
        self.assertEqual(302, response.status_code)
        self.assertEqual(TEST_SITE + '/foo', response['Location'])

    def test_tricky_redirection_replaced(self):
        # 'next' argument is not signed, so can be replaced by the
        # user. This is OK as long as all tricky paths are replaced.
        self.site.users.create_item('foo@example.org')
        token = generate_login_token(self.site, TEST_SITE, 'foo@example.org')
        params = urllib.urlencode(dict(token=token, next='www.example.com'))
        response = self.get('/auth/api/login/?' + params)
        self.assertEqual(302, response.status_code)
        # Ignore 'next' argument from the login URL
        self.assertEqual(TEST_SITE + '/', response['Location'])

    def test_successful_login_invalidates_token(self):
        self.site.users.create_item('foo@example.org')
        token = generate_login_token(self.site, TEST_SITE, 'foo@example.org')
        response = self.get('/auth/api/login/?token=' + token)
        self.assertEqual(302, response.status_code)
        response = self.get('/auth/api/login/?token=' + token)
        self.assertEqual(400, response.status_code)
        self.assertEqual('Token invalid or expired.', response.content)

class SessionCacheTest(AuthTestCase):
    def test_user_cached_in_session(self):
        user = self.site.users.create_item('foo@example.com')

        token = generate_login_token(self.site, TEST_SITE, 'foo@example.com')
        params = urllib.urlencode(dict(token=token, next='/foo'))
        response = self.get('/auth/api/login/?' + params)
        self.assertEqual(302, response.status_code)

        s = self.client.session
        user_id = s['user_id']
        self.assertIsNotNone(user_id)
        self.assertEqual(user_id, user.id)
