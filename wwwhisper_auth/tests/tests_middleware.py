# wwwhisper - web access control.
# Copyright (C) 2012, 2013 Jan Wrobel <wrr@mixedbit.org>
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

from django.http import HttpRequest
from django.test import TestCase
from wwwhisper_auth import http
from wwwhisper_auth.middleware import SecuringHeadersMiddleware
from wwwhisper_auth.middleware import ProtectCookiesMiddleware
from wwwhisper_auth.middleware import SetSiteMiddleware
from wwwhisper_auth.middleware import SiteUrlMiddleware
from wwwhisper_auth.models import SitesCollection
from wwwhisper_auth.models import SINGLE_SITE_ID

class SetSiteMiddlewareTest(TestCase):
    def test_site_set_if_exists(self):
        site = SitesCollection().create_item(SINGLE_SITE_ID)
        middleware = SetSiteMiddleware()
        r = HttpRequest()
        self.assertIsNone(middleware.process_request(r))
        self.assertEqual(SINGLE_SITE_ID, r.site.site_id)

    def test_site_not_set_if_missing(self):
        middleware = SetSiteMiddleware()
        r = HttpRequest()
        self.assertIsNone(middleware.process_request(r))
        self.assertIsNone(r.site)

class SiteUrlMiddlewareTest(TestCase):
    def setUp(self):
        self.middleware = SiteUrlMiddleware()
        self.request = HttpRequest()
        self.sites = SitesCollection()
        self.request.site = self.sites.create_item(SINGLE_SITE_ID)
        self.site_url = 'https://foo.example.com'
        self.request.site.aliases.create_item(self.site_url)

    def test_allowed_site_url_https(self):
        self.request.META['HTTP_SITE_URL'] = self.site_url
        self.assertIsNone(self.middleware.process_request(self.request))
        self.assertEqual(self.site_url, self.request.site_url)
        self.assertEqual('foo.example.com', self.request.get_host())
        self.assertTrue(self.request.https)
        self.assertTrue(self.request.is_secure())

    def test_allowed_site_url_http(self):
        url = 'http://bar.example.com'
        self.request.site.aliases.create_item(url)
        self.request.META['HTTP_SITE_URL'] = url
        self.assertIsNone(self.middleware.process_request(self.request))
        self.assertEqual(url, self.request.site_url)
        self.assertEqual('bar.example.com', self.request.get_host())
        self.assertFalse(self.request.https)
        self.assertFalse(self.request.is_secure())

    def test_allowed_site_url_with_port(self):
        url = 'http://bar.example.com:123'
        self.request.site.aliases.create_item(url)
        self.request.META['HTTP_SITE_URL'] = url
        self.assertIsNone(self.middleware.process_request(self.request))
        self.assertEqual(url, self.request.site_url)
        self.assertEqual('bar.example.com:123', self.request.get_host())
        self.assertFalse(self.request.https)
        self.assertFalse(self.request.is_secure())

    def test_not_allowed_site_url(self):
        self.request.META['HTTP_SITE_URL'] = 'https://bar.example.com'
        response = self.middleware.process_request(self.request)
        self.assertIsNotNone(response)
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(response.content,
                                 'Invalid request URL')

    def test_not_allowed_site_url2(self):
        self.request.META['HTTP_SITE_URL'] = 'https://foo.example.com:80'
        response = self.middleware.process_request(self.request)
        self.assertIsNotNone(response)
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(response.content,
                                 'Invalid request URL')

    def test_missing_site_url(self):
        response = self.middleware.process_request(self.request)
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(response.content,
                                 'Missing Site-Url header')

    def test_invalid_site_url(self):
        self.request.META['HTTP_SITE_URL'] = 'foo.example.org'
        response = self.middleware.process_request(self.request)
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(response.content,
                                 'Site-Url has incorrect format')

    def test_allowed_site_with_explicit_port(self):
        # Request with correct explicit port should be accepted, port
        # should be removed.
        self.request.META['HTTP_SITE_URL'] = self.site_url + ':443'
        self.assertIsNone(self.middleware.process_request(self.request))
        self.assertEqual(self.site_url, self.request.site_url)
        self.assertEqual('foo.example.com', self.request.get_host())
        self.assertTrue(self.request.https)
        self.assertTrue(self.request.is_secure())

    def test_not_allowed_http_site_redirects_to_https_if_exists(self):
        self.request.META['HTTP_SITE_URL'] = 'http://foo.example.com'
        self.request.path = '/bar?baz=true'
        response = self.middleware.process_request(self.request)
        self.assertIsNotNone(response)
        self.assertEqual(302, response.status_code)
        self.assertEqual('https://foo.example.com/bar?baz=true',
                         response['Location'])

    def test_https_redirects_for_auth_request(self):
        self.request.META['HTTP_SITE_URL'] = 'http://foo.example.com'
        self.request.path = '/auth/api/is-authorized/?path=/foo/bar/baz'
        response = self.middleware.process_request(self.request)
        self.assertIsNotNone(response)
        self.assertEqual(302, response.status_code)
        self.assertEqual('https://foo.example.com/foo/bar/baz',
                         response['Location'])

class ProtectCookiesMiddlewareTest(TestCase):

    def test_secure_flag_set_for_https_request(self):
        middleware = ProtectCookiesMiddleware()
        request = HttpRequest()
        request.https = True
        response = http.HttpResponseNoContent()
        response.set_cookie('session', value='foo', secure=None)

        self.assertFalse(response.cookies['session']['secure'])
        response = middleware.process_response(request, response)
        self.assertTrue(response.cookies['session']['secure'])

    def test_secure_flag_not_set_for_http_request(self):
        middleware = ProtectCookiesMiddleware()
        request = HttpRequest()
        request.https = False
        response = http.HttpResponseNoContent()
        response.set_cookie('session', value='foo', secure=None)

        self.assertFalse(response.cookies['session']['secure'])
        response = middleware.process_response(request, response)
        self.assertFalse(response.cookies['session']['secure'])


class SecuringHeadersMiddlewareTest(TestCase):

    def test_different_origin_framing_not_allowed(self):
        middleware = SecuringHeadersMiddleware()
        request = HttpRequest()
        response = http.HttpResponseNoContent()
        self.assertFalse('X-Frame-Options' in response)
        self.assertFalse('X-Content-Type-Options' in response)
        response = middleware.process_response(request, response)
        self.assertEqual('SAMEORIGIN', response['X-Frame-Options'])
        self.assertEqual('nosniff', response['X-Content-Type-Options'])
