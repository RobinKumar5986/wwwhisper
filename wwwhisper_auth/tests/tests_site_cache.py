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
from mock import Mock
from wwwhisper_auth.site_cache import SiteCache

class FakeCacheUpdater(object):
    def __init__(self):
        self.return_value = False

    def is_obsolete(self, site):
        return self.return_value

class SiteCacheTest(TestCase):

    def setUp(self):
        self.updater = FakeCacheUpdater()
        self.cache = SiteCache(self.updater)

    def test_cache(self):
        site = Mock()
        site.site_id = 'foo'
        self.assertIsNone(self.cache.get('foo'))
        self.cache.insert(site)
        self.assertEqual(site, self.cache.get('foo'))
        self.assertIsNone(self.cache.get('bar'))
        self.cache.delete('foo')
        self.assertIsNone(self.cache.get('foo'))

    def test_cache_obsolete(self):
        site = Mock()
        site.site_id = 'foo'
        self.cache.insert(site)
        self.assertEqual(site, self.cache.get('foo'))
        # Configure cache updater to obsolete the cached element.
        self.updater.return_value = True
        self.assertIsNone(self.cache.get('foo'))
