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

from django.test import TestCase
from wwwhisper_auth.site import SiteMiddleware
from mock import Mock

class SiteMiddlewareTest(TestCase):

    def create_request(self):
        r = Mock()
        r.META = {}
        return r

    def test_site_from_settings(self):
        site_url = 'http://foo.example.org'
        middleware = SiteMiddleware(site_url)
        r = self.create_request()

        self.assertIsNone(middleware.process_request(r))
        self.assertEqual(site_url, r.site_id)
        self.assertEqual(site_url, r.site_url)

    def test_site_from_frontend(self):
        site_url = 'http://foo.example.org'
        middleware = SiteMiddleware(None)
        r = self.create_request()
        r.META['HTTP_SITE_URL'] = site_url
        self.assertIsNone(middleware.process_request(r))
        self.assertEqual(None, r.site_id)
        self.assertEqual(site_url, r.site_url)


    def test_missing_site_from_frontend(self):
        r = self.create_request()
        middleware = SiteMiddleware(None)
        response = middleware.process_request(r)
        self.assertEqual(400, response.status_code)


    def test_is_https(self):
        r = self.create_request()
        middleware = SiteMiddleware('http://foo.com')
        self.assertIsNone(middleware.process_request(r))
        self.assertFalse(r.https)

        middleware = SiteMiddleware('https://foo.com')
        self.assertIsNone(middleware.process_request(r))
        self.assertTrue(r.https)

        middleware = SiteMiddleware(None)
        r.META['HTTP_SITE_URL'] = 'http://bar.example.org'
        self.assertIsNone(middleware.process_request(r))
        self.assertFalse(r.https)


        middleware = SiteMiddleware(None)
        r.META['HTTP_SITE_URL'] = 'https://bar.example.org'
        self.assertIsNone(middleware.process_request(r))
        self.assertTrue(r.https)
