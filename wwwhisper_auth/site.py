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

from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from wwwhisper_auth import http

SITE_URL = getattr(settings, 'SITE_URL', None)
if SITE_URL is None:
    raise ImproperlyConfigured(
        'WWWhisper requires SITE_URL to be set in django settings.py file')

SITE_URL_FROM_FRONT_END = getattr(
    settings, 'SITE_URL_FROM_FRONT_END', False)

class SiteMiddleware(object):
    #TODO: document.
    #TODO: allow to pass site id from backend.

    def _is_https(self, url):
        return (url[:8].lower() == 'https://')

    def __init__(self, site_url=SITE_URL,
                 site_url_from_front_end=SITE_URL_FROM_FRONT_END):
        self.site_url = site_url
        self.site_url_from_front_end = site_url_from_front_end
        self.https = self._is_https(self.site_url)

    """Sets site id and site url for a request."""
    def process_request(self, request):
        if self.site_url_from_front_end:
            request.site_id = None
            request.site_url = request.META.get('HTTP_SITE_URL', None)
            if (request.site_url is None):
                return http.HttpResponseBadRequest('Missing SITE_URL header')
            request.https = self._is_https(request.site_url)
        else:
            request.site_id = self.site_url
            request.site_url = self.site_url
            request.https = self.https
        return None
