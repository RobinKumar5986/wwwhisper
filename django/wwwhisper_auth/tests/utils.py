from django.test import TestCase
from django.test.client import Client

import json

class HttpTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.common_args = {}
        self.common_args['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

    def post(self, url, args):
        return self.client.post(url,
                                json.dumps(args),
                                'text/json',
                                **self.common_args)

    def get(self, url):
        return self.client.get(url, **self.common_args)

    def put(self, url, args=None):
        if args is None:
            return self.client.put(url, **self.common_args)
        return self.client.put(
            url, json.dumps(args), 'text/json', **self.common_args)


    def delete(self, url):
        return self.client.delete(url, **self.common_args)


