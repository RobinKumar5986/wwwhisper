from django.test import TestCase
from django.test.client import Client

from tests_acl import *
from tests_views import *

import json

# TODO: use it in auth tests.
class HttpTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    # TODO: rename without json_?
    def json_post(self, url, args):
        # TODO: remove duplication.
        return self.client.post(url,
                                json.dumps(args),
                                'text/json',
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def json_get(self, url):
        return self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def json_put(self, url, args):
        return self.client.put(url,
                               json.dumps(args),
                               'text/json',
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')


    def json_delete(self, url):
        return self.client.delete(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

