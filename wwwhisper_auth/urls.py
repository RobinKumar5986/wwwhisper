# wwwhisper - web access control.
# Copyright (C) 2012-2015 Jan Wrobel <jan@mixedbit.org>
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

"""Urls exposed by the wwwhisper_auth application.

is-authorized/ URL does not need to be exposed by the HTTP server to
the outside world, other views need to be externally accessible.
"""

from django.conf import settings
from django.conf.urls import patterns, url
from wwwhisper_auth.views import Auth, CsrfToken, Login, Logout, WhoAmI

urlpatterns = patterns(
    'wwwhisper_auth.views',
    url(r'^csrftoken/$', CsrfToken.as_view()),
    url(r'^login/$', Login.as_view()),
    url(r'^logout/$', Logout.as_view()),
    url(r'^whoami/$', WhoAmI.as_view()),
    url(r'^is-authorized/$', Auth.as_view(), name='auth-request'),
    )
