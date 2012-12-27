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

"""Urls exposed by the wwwhisper_admin application."""

from django.conf.urls.defaults import patterns, url
from views import CollectionView, ItemView
from views import OpenAccessView, AllowedUsersView
from wwwhisper_auth import models

users_collection = models.UsersCollection()
locations_collection = models.LocationsCollection()

urlpatterns = patterns(
    'wwwhisper_admin.views',
    url(r'^users/$',
        CollectionView.as_view(collection=users_collection)),
    url(r'^users/(?P<uuid>[0-9a-z-]+)/$',
        ItemView.as_view(collection=users_collection),
        name='wwwhisper_user'),
    url(r'^locations/$',
        CollectionView.as_view(collection=locations_collection)),
    url(r'^locations/(?P<uuid>[0-9a-z-]+)/$',
        ItemView.as_view(collection=locations_collection),
        name='wwwhisper_location'),
    url(r'^locations/(?P<location_uuid>[0-9a-z-]+)/allowed-users/' +
        '(?P<user_uuid>[0-9a-z-]+)/$',
        AllowedUsersView.as_view(locations_collection=locations_collection),
        name='wwwhisper_allowed_user'),
    url(r'^locations/(?P<location_uuid>[0-9a-z-]+)/open-access/$',
        OpenAccessView.as_view(locations_collection=locations_collection)),
    )
