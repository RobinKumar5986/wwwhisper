"""Utilities to simplify testing."""

from django.test import TestCase
from django.test.client import Client

import json

class HttpTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def post(self, url, args):
        return self.client.post(url, json.dumps(args), 'text/json')

    def get(self, url):
        return self.client.get(url)

    def put(self, url, args=None):
        if args is None:
            return self.client.put(url)
        return self.client.put(url, json.dumps(args), 'text/json')


    def delete(self, url):
        return self.client.delete(url)


