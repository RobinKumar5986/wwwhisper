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

from django.conf import settings
from django.conf.urls.defaults import patterns, url
from django.http import HttpResponse
from django.test import TestCase
from django.test.client import Client
from wwwhisper_auth.http import accepts_html
from wwwhisper_auth.http import RestView
from wwwhisper_auth.tests.utils import HttpTestCase

class TestView(RestView):
    def get(self, request):
        return HttpResponse(status=267)

    def post(self, request, ping_message):
        return HttpResponse(ping_message, status=277)

class TestView2(RestView):
    def get(self, request, url_arg):
        return HttpResponse(url_arg, status=288)

    def post(self, request, url_arg):
        return HttpResponse(url_arg, status=298)

urlpatterns = patterns(
    '',
    url(r'^testview/$', TestView.as_view()),
    url(r'^testview2/(?P<url_arg>[a-z]+)/$', TestView2.as_view()))

class RestViewTest(HttpTestCase):
    urls = 'wwwhisper_auth.tests.tests_http'

    def test_method_dispatched(self):
        response = self.get('/testview/')
        self.assertEqual(267, response.status_code)

    def test_method_with_json_argument_in_body_dispatched(self):
        response = self.post('/testview/', {'ping_message' : 'hello world'})
        self.assertEqual(277, response.status_code)
        self.assertEqual('hello world', response.content)

    def test_method_with_missing_json_argument_in_body_dispatched(self):
        response = self.post('/testview/', {})
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(response.content, 'Invalid request arguments')

    def test_method_with_incorrect_json_argument_in_body(self):
        response = self.post('/testview/', {'pong_message' : 'hello world'})
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(response.content, 'Invalid request arguments')

    def test_method_with_incorrectly_formated_json_argument_in_body(self):
        response = self.client.post('/testview/',
                                    "{{ 'ping_message' : 'hello world' }",
                                    'application/json ;  charset=UTF-8',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(response.content, 'Failed to parse the '
                                 'request body as a json object.')

    def test_incorrect_method(self):
        response = self.delete('/testview/')
        self.assertEqual(405, response.status_code)
        # 'The response MUST include an Allow header containing a list
        # of valid methods for the requested resource.' (rfc2616)
        self.assertItemsEqual(['GET', 'POST', 'HEAD', 'OPTIONS'],
                              response['Allow'].split(', '))

    def test_method_with_argument_in_url_dispatched(self):
        response = self.get('/testview2/helloworld/')
        self.assertEqual(288, response.status_code)
        self.assertEqual('helloworld', response.content)


    def test_argument_in_body_cannot_overwrite_argument_in_url(self):
        response = self.post('/testview2/helloworld/',
                             {'url_arg': 'hello-world'})
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(
            response.content, 'Invalid argument passed in the request body.')

    def test_content_type_validation(self):
        response = self.client.post(
            '/testview/', '{"ping_message" : "hello world"}', 'text/json')
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(response.content,
                                 'Invalid Content-Type')

        response = self.client.post(
            '/testview/', '{"ping_message" : "hello world"}',
            'application/json; charset=UTF-16')
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(response.content,
                                 'Invalid Content-Type')

        # Content-Type header should be case-insensitive.
        response = self.client.post(
            '/testview/', '{"ping_message" : "hello world"}',
            'application/JSON; charset=UTF-8')
        self.assertEqual(277, response.status_code)

    def test_csrf_protection(self):
        self.client = Client(enforce_csrf_checks=True)

        # No CSRF tokens.
        response = self.client.get('/testview/')
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(response.content,
                                 'CSRF token missing or incorrect')

        # Too short CSRF tokens.
        self.client.cookies[settings.CSRF_COOKIE_NAME] = 'a'
        response = self.client.get('/testview/', HTTP_X_CSRFTOKEN='a')
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(response.content,
                                 'CSRF token missing or incorrect')

        # Not matching CSRF tokens.
        self.client.cookies[settings.CSRF_COOKIE_NAME] = \
            'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
        response = self.client.get(
            '/testview/', HTTP_X_CSRFTOKEN='xxxxxxxxxxxxxxxOxxxxxxxxxxxxxxxx')
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(response.content,
                                 'CSRF token missing or incorrect')

        # Matching CSRF tokens.
        self.client.cookies[settings.CSRF_COOKIE_NAME] = \
            'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
        response = self.client.get(
            '/testview/', HTTP_X_CSRFTOKEN='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        self.assertEqual(267, response.status_code)

    def test_caching_disabled_for_rest_view_results(self):
        response = self.get('/testview/')
        self.assertTrue(response.has_header('Cache-Control'))
        control = response['Cache-Control']
        # index throws ValueError if not found.
        control.index('no-cache')
        control.index('no-store')
        control.index('must-revalidate')
        control.index('max-age=0')


class AcceptHeaderUtilsTest(TestCase):
    def test_accepts_html(self):
        self.assertTrue(accepts_html('text/html'))
        self.assertTrue(accepts_html('text/*'))
        self.assertTrue(accepts_html('*/*'))
        self.assertTrue(accepts_html('audio/*, text/plain, text/*'))
        self.assertTrue(accepts_html(
                'text/*;q=0.3, text/html;q=0.7, text/html;level=1, ' +
                'text/html;level=2;q=0.4, */*;q=0.5'))

        self.assertFalse(accepts_html('text/plain'))
        self.assertFalse(accepts_html('audio/*'))
        self.assertFalse(accepts_html('text/x-dvi; q=0.8, text/x-c'))
        self.assertFalse(accepts_html(None))
