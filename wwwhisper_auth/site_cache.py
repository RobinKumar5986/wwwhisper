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

"""Cache for sites with all associated data.

If the site was not modified since it was stored in the cache all data
(locations, users and permissions) are taken from the cache.

Majority of wwwhisper request are performance critical
auth-requests. Because these requests are read only, caching is very
efficient (cached data rarely needs to be updated).
"""

from django.db import connection

import logging

logger = logging.getLogger(__name__)

class CacheUpdater(object):
    """Checks if the cached site needs to be updated.

    This is a simple, database agnostic implementation that runs a
    single query against the site table to check if the site
    modification token has changed.
    """

    def is_obsolete(self, site):
        mod_id = site.mod_id_from_db(connection)
        return mod_id is None or mod_id != site.mod_id

class SiteCache(object):
    def __init__(self, updater=CacheUpdater()):
        self._updater = updater
        self._items = {}

    def insert(self, site):
        self._items[site.site_id] = site

    def get(self, site_id):
        site = self._items.get(site_id, None)
        if site is None:
            return None
        if self._updater.is_obsolete(site):
            self.delete(site_id)
            return None
        return site

    def delete(self, site_id):
        self._items.pop(site_id, None)
