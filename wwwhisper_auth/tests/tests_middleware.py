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

from django.conf import settings
from django.http import HttpRequest
from django.test import TestCase
from mock import Mock
from wwwhisper_auth import http
from wwwhisper_auth.middleware import ProtectCookiesMiddleware
from wwwhisper_auth.middleware import SiteMiddleware
from wwwhisper_auth.models import SitesCollection

class SiteMiddlewareFromSettingsTest(TestCase):

    def test_site_from_settings(self):
        site_url = 'http://foo.example.org'
        site = SitesCollection().create_item(site_url)
        middleware = SiteMiddleware(site_url)
        r = HttpRequest()

        self.assertIsNone(middleware.process_request(r))
        self.assertTrue(site is r.site)
        self.assertEqual(site_url, r.site.site_id)
        self.assertEqual(site_url, r.site_url)

    def test_site_from_settings_if_no_such_site(self):
        site_url = 'http://foo.example.org'
        middleware = SiteMiddleware(site_url)
        r = HttpRequest()

        self.assertIsNone(middleware.process_request(r))
        self.assertIsNone(r.site)
        self.assertEqual(site_url, r.site_url)

    def test_is_https(self):
        r = HttpRequest()
        middleware = SiteMiddleware('http://foo.com')
        self.assertIsNone(middleware.process_request(r))
        self.assertFalse(r.https)

        middleware = SiteMiddleware('https://foo.com')
        self.assertIsNone(middleware.process_request(r))
        self.assertTrue(r.https)


class SiteMiddlewareFromFrontendTest(TestCase):

    def setUp(self):
        settings.USE_X_FORWARDED_HOST = True
        settings.SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    def tearDown(self):
        settings.USE_X_FORWARDED_HOST = False
        settings.SECURE_PROXY_SSL_HEADER = None

    def test_site_from_frontend(self):
        site_url = 'http://foo.example.org'
        middleware = SiteMiddleware(None)
        r = HttpRequest()
        r.META['HTTP_SITE_URL'] = site_url
        self.assertIsNone(middleware.process_request(r))
        self.assertEqual(None, r.site)
        self.assertEqual(site_url, r.site_url)
        self.assertEqual('foo.example.org', r.get_host())
        self.assertFalse(r.https)
        self.assertFalse(r.is_secure())

    def test_https_site_from_frontend(self):
        site_url = 'https://foo.example.org'
        middleware = SiteMiddleware(None)
        r = HttpRequest()
        r.META['HTTP_SITE_URL'] = site_url
        self.assertIsNone(middleware.process_request(r))
        self.assertEqual(None, r.site)
        self.assertEqual(site_url, r.site_url)
        self.assertEqual('foo.example.org', r.get_host())
        self.assertTrue(r.https)
        self.assertTrue(r.is_secure())

    def test_missing_site_from_frontend(self):
        r = HttpRequest()
        middleware = SiteMiddleware(None)
        response = middleware.process_request(r)
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(response.content,
                                 'Missing Site-Url header')

    def test_invalid_site_from_frontend(self):
        r = HttpRequest()
        r.META['HTTP_SITE_URL'] = 'foo.example.org'
        middleware = SiteMiddleware(None)
        response = middleware.process_request(r)
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(response.content,
                                 'Site-Url has incorrect format')

    def test_is_https(self):
        r = HttpRequest()
        middleware = SiteMiddleware(None)
        r.META['HTTP_SITE_URL'] = 'http://bar.example.org'
        self.assertIsNone(middleware.process_request(r))
        self.assertFalse(r.https)

        middleware = SiteMiddleware(None)
        r.META['HTTP_SITE_URL'] = 'https://bar.example.org'
        self.assertIsNone(middleware.process_request(r))
        self.assertTrue(r.https)


class ProtectCookiesMiddlewareTest(TestCase):

    def create_request(self):
        r = Mock()
        r.META = {}
        return r

    def test_secure_flag_set_for_https_request(self):
        middleware = ProtectCookiesMiddleware()
        request = self.create_request()
        request.https = True
        response = http.HttpResponseNoContent()
        response.set_cookie('session', value='foo', secure=None)

        self.assertFalse(response.cookies['session']['secure'])
        response = middleware.process_response(request, response)
        self.assertTrue(response.cookies['session']['secure'])

    def test_secure_flag_not_set_for_http_request(self):
        middleware = ProtectCookiesMiddleware()
        request = self.create_request()
        request.https = False
        response = http.HttpResponseNoContent()
        response.set_cookie('session', value='foo', secure=None)

        self.assertFalse(response.cookies['session']['secure'])
        response = middleware.process_response(request, response)
        self.assertFalse(response.cookies['session']['secure'])

