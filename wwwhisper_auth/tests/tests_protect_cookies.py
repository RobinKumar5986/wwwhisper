# wwwhisper - web access control.
# Copyright (C) 2013 Jan Wrobel <wrr@mixedbit.org>
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
from wwwhisper_auth.protect_cookies import ProtectCookiesMiddleware
from wwwhisper_auth import http
from mock import Mock

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

