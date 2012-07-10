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

"""Views that allow to manage access control list.

Expose REST interface for adding/removing locations and users and for
granting/revoking access to locations.
"""

from wwwhisper_auth import http
from wwwhisper_auth.models import CreationException
from wwwhisper_auth.models import full_url

import logging

logger = logging.getLogger(__name__)

class CollectionView(http.RestView):
    """Generic view over a collection of resources.

    Allows to get json representation of all resources in the
    collection and to add new resources to the collection.

    Attributes:
        collection: The collection that view represents (extends
        wwwhisper_auth.models.Collection).
    """
    collection = None

    def post(self, request, **kwargs):
        """Ads a new resource to the collection.

        Args:
            **kwargs: holds collection dependent arguments that are
              used to create the resource.
        Returns json representation of the added resource."""
        try:
            created_item = self.collection.create_item(**kwargs)
        except CreationException as ex:
            return http.HttpResponseBadRequest(ex)
        attributes_dict = created_item.attributes_dict()
        response = http.HttpResponseCreated(attributes_dict)
        response['Location'] = attributes_dict['self']
        response['Content-Location'] = attributes_dict['self']
        return response

    def get(self, request):
        """Returns json representation of all resources in the collection."""
        items_list = [item.attributes_dict() for item in self.collection.all()]
        return http.HttpResponseOKJson({
                'self' : full_url(request.path),
                self.collection.collection_name: items_list
                })

class ItemView(http.RestView):
    """Generic view over a single resource stored in a collection.

    Allows to get json representation of the resource and to delete
    the resource.

    Attributes:
        collection: The collection that view uses to retrieve the resource
        (extends wwwhisper_auth.models.Collection).
    """

    collection = None

    def get(self, request, uuid):
        """Returns json representation of a resource with a given uuid."""
        item = self.collection.find_item(uuid)
        if item is None:
            return http.HttpResponseNotFound(
                '%s not found' % self.collection.item_name.capitalize())
        return http.HttpResponseOKJson(item.attributes_dict())

    def delete(self, request, uuid):
        """Deletes a resource with a given uuid."""
        deleted = self.collection.delete_item(uuid)
        if not deleted:
            return http.HttpResponseNotFound(
                '%s not found' % self.collection.item_name.capitalize())
        return http.HttpResponseNoContent()

class OpenAccessView(http.RestView):
    """Manages resources that define if a location requires authorization.

    Attributes:
        location_collection: The collection that is used to find
        a location to which requests are related.
    """
    locations_collection = None

    @staticmethod
    def _attributes_dict(request):
        """Attributes representing a resource to which a request is related."""
        return {'self' : full_url(request.path)}

    def put(self, request, location_uuid):
        """Creates a resource that enables open access to a given location."""
        location = self.locations_collection.find_item(location_uuid)
        if location is None:
            return http.HttpResponseNotFound('Location not found.')
        if location.open_access:
            return http.HttpResponseOKJson(self._attributes_dict(request))

        location.grant_open_access()
        response =  http.HttpResponseCreated(self._attributes_dict(request))
        response['Location'] = full_url(request.path)
        return response

    def get(self, request, location_uuid):
        """Check if a resource that enables open access to a location exists."""
        location = self.locations_collection.find_item(location_uuid)
        if location is None:
            return http.HttpResponseNotFound('Location not found.')
        if location.open_access is False:
            return http.HttpResponseNotFound(
                'Open access to location disallowed.')
        return http.HttpResponseOKJson(self._attributes_dict(request))

    def delete(self, request, location_uuid):
        """Deletes a resource.

        Disables open access to a given location.
        """
        location = self.locations_collection.find_item(location_uuid)
        if location is None:
            return http.HttpResponseNotFound('Location not found.')
        if location.open_access is False:
            return http.HttpResponseNotFound(
                'Open access to location already disallowed.')
        location.revoke_open_access()
        return http.HttpResponseNoContent()

class AllowedUsersView(http.RestView):
    """Manages resources that define which users can access locations.

    Attributes:
        location_collection: The collection that is used to find
        location to which requests are related.
    """
    locations_collection = None

    def put(self, request, location_uuid, user_uuid):
        """Creates a resource.

        Grants access to a given location by a given user.
        """
        location = self.locations_collection.find_item(location_uuid)
        if not location:
            return http.HttpResponseNotFound('Location not found.')
        try:
            (permission, created) = location.grant_access(user_uuid)
            attributes_dict = permission.attributes_dict()
            if created:
                response =  http.HttpResponseCreated(attributes_dict)
                response['Location'] = attributes_dict['self']
            else:
                response = http.HttpResponseOKJson(attributes_dict)
            return response
        except LookupError as ex:
            return http.HttpResponseNotFound(str(ex))

    def get(self, request, location_uuid, user_uuid):
        """Checks if a resource that grants access exists.

        This is not equivalent of checking if the user can access the
        location. If the location is open, but the user is not
        explicitly granted access, not found failure is returned.
        """
        location = self.locations_collection.find_item(location_uuid)
        if location is None:
            return http.HttpResponseNotFound('Location not found.')
        try:
            permission = location.get_permission(user_uuid)
            return http.HttpResponseOKJson(permission.attributes_dict())
        except LookupError as ex:
            return http.HttpResponseNotFound(str(ex))

    def delete(self, request, location_uuid, user_uuid):
        """Deletes a resource

        Revokes access to a given location by a given user. If the
        location is open, the user will still be able to access the
        location after this call succeeds.
        """
        location = self.locations_collection.find_item(location_uuid)
        if not location:
            return http.HttpResponseNotFound('Location not found.')
        try:
            location.revoke_access(user_uuid)
            return http.HttpResponseNoContent()
        except LookupError as ex:
            return http.HttpResponseNotFound(str(ex))
