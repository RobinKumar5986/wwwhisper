# wwwhisper - web access control.
# Copyright (C) 2012 Jan Wrobel <wrr@mixedbit.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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


