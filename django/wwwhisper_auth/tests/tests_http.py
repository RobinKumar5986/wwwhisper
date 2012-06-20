from django.http import HttpResponse
from django.test import TestCase
from wwwhisper_auth.http import RestView
from wwwhisper_auth.tests.utils import HttpTestCase
from django.conf.urls.defaults import patterns, url

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
                                    'text/json',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(400, response.status_code)
        self.assertRegexpMatches(response.content, 'Failed to parse the '
                                 'request body as a json object.')

    def test_incorrect_method(self):
        response = self.delete('/testview/')
        self.assertEqual(405, response.status_code)
        # 'The response MUST include an Allow header containing a list
        # of valid methods for the requested resource.' (rfc2616)
        self.assertItemsEqual(['get', 'post', 'head'],
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
