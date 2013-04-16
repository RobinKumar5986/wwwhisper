# wwwhisper - web access control.
# Copyright (C) 2012, 2013 Jan Wrobel <wrr@mixedbit.org>
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

import wwwhisper_auth.site_cache
import logging

logger = logging.getLogger(__name__)

SITE_URL_FROM_FRONT_END = getattr(
    settings, 'SITE_URL_FROM_FRONT_END', False)

SITE_URL = getattr(settings, 'SITE_URL', None)

if not SITE_URL and not SITE_URL_FROM_FRONT_END:
    raise ImproperlyConfigured(
        'wwwhisper requires either SITE_URL or SITE_URL_FROM_FRONTEND ' +
        'to be set in Django settings.py file')

if SITE_URL and SITE_URL_FROM_FRONT_END:
    raise ImproperlyConfigured(
        'SITE_URL and SITE_URL_FROM_FRONTEND can not be set together.')


class SiteMiddleware(object):
    """Determines to which site a request is related"""

    def _is_https(self, url):
        return (url[:5].lower() == 'https')

    def __init__(self, site_url=SITE_URL):
        self.sites = wwwhisper_auth.site_cache.CachingSitesCollection()
        self.site_url_from_front_end = (site_url is None)
        if not self.site_url_from_front_end:
            self.site_url = site_url

    """Sets site_url and (optionally) site to which request is related."""
    def process_request(self, request):
        if self.site_url_from_front_end:
            # Site needs to be set by a separate middleware.
            request.site = None
            request.site_url = request.META.get('HTTP_SITE_URL', None)
            if request.site_url is None:
                return http.HttpResponseBadRequest('Missing Site-Url header')
            parts = request.site_url.split('://')
            if len(parts) != 2:
                return http.HttpResponseBadRequest(
                    'Site-Url has incorrect format')
            scheme, host = parts
            request.META[settings.SECURE_PROXY_SSL_HEADER[0]] = scheme
            request.META['HTTP_X_FORWARDED_HOST'] = host
        else:
            request.site = self.sites.find_item(self.site_url)
            request.site_url = self.site_url

        request.https = self._is_https(request.site_url)
        return None


class ProtectCookiesMiddleware(object):
    """Sets 'secure' flag for all cookies if request is over https.

    The flag prevents cookies from being sent with HTTP requests.
    """

    def process_response(self, request, response):
        # response.cookies is SimpleCookie (Python 'Cookie' module).
        for cookie in response.cookies.itervalues():
            if request.https:
                cookie['secure'] = True
        return response


class SecuringHeadersMiddleware(object):
    """Sets headers that impede clickjacking + content sniffing related attacks.
    """

    def process_response(self, request, response):
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['X-Content-Type-Options'] = 'nosniff'
        return response
