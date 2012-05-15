from django.test import TestCase
from django.test.client import Client

from tests_acl import *
from tests_views import *

import json

# TODO: use it in auth tests.
class HttpTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def json_post(self, path, args):
        # TODO: remove duplication.
        return self.client.post(path,
                                json.dumps(args),
                                'text/json',
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def json_put(self, path, args):
        return self.client.put(path,
                               json.dumps(args),
                               'text/json',
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')


    def json_delete(self, path, args):
        return self.client.delete(path,
                                  json.dumps(args),
                                  'text/json',
                                  HTTP_X_REQUESTED_WITH='XMLHttpRequest')

