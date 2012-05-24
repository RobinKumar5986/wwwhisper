from django.test import TestCase
from django.test.client import Client

from tests_models import *
from tests_views import *

import json

# TODO: use it in auth tests.
class HttpTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def post(self, url, args):
        # TODO: remove duplication.
        return self.client.post(url,
                                json.dumps(args),
                                'text/json',
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def get(self, url):
        return self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def put(self, url):
        return self.client.put(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')


    def delete(self, url):
        return self.client.delete(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

