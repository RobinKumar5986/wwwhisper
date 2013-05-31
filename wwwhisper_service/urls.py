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

from django.conf import settings
from django.conf.urls import include, patterns, url
from django.conf import settings
from wwwhisper_auth.assets import Asset, HtmlFileView, JsFileView

import logging

logger = logging.getLogger(__name__

def _add_suffix(suffix):
    return r'^%s%s' % (settings.WWWHISPER_PATH_PREFIX, suffix)

def _url(path, *args):
    return url(_add_suffix(path), *args)

urlpatterns = patterns(
    '',
    _url(r'auth/api/', include('wwwhisper_auth.urls')),
    _url(r'admin/api/', include('wwwhisper_admin.urls')),
    )

if settings.WWWHISPER_STATIC is not None:
    logger.debug('wwwhisper configured to serve static files.')
    admin = Asset(settings.WWWHISPER_STATIC, 'admin', 'index.html')
    overlay = Asset(settings.WWWHISPER_STATIC, 'auth', 'overlay.html')
    iframe = Asset(settings.WWWHISPER_STATIC, 'auth', 'iframe.js')
    logout = Asset(settings.WWWHISPER_STATIC, 'auth', 'logout.html')
    goodbye = Asset(settings.WWWHISPER_STATIC, 'auth', 'goodbye.html')

    urlpatterns += patterns(
        '',
        _url('admin/$', HtmlFileView.as_view(asset=admin)),
        _url('auth/overlay.html$', HtmlFileView.as_view(asset=overlay)),
        _url('auth/iframe.js$', JsFileView.as_view(asset=iframe)),
        _url('auth/logout/$', HtmlFileView.as_view(asset=logout)),
        _url('auth/logout.html$', HtmlFileView.as_view(asset=logout)),
        _url('auth/goodbye.html$', HtmlFileView.as_view(asset=goodbye)),
        )

