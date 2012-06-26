"""Views that allow to manage access control list.

Expose REST interface for adding/removing locations and users and for
granting/revoking access to locations.
"""

from django.http import HttpResponseNotFound
from wwwhisper_auth.http import HttpResponseBadRequest
from wwwhisper_auth.http import HttpResponseCreated
from wwwhisper_auth.http import HttpResponseJson
from wwwhisper_auth.http import HttpResponseNoContent
from wwwhisper_auth.http import RestView
from wwwhisper_auth.models import CreationException
from wwwhisper_auth.models import full_url

import logging

logger = logging.getLogger(__name__)

class CollectionView(RestView):
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
            return HttpResponseBadRequest(ex)
        attributes_dict = created_item.attributes_dict()
        response = HttpResponseCreated(attributes_dict)
        response['Location'] = attributes_dict['self']
        response['Content-Location'] = attributes_dict['self']
        return response

    def get(self, request):
        """Returns json representation of all resources in the collection."""
        items_list = [item.attributes_dict() for item in self.collection.all()]
        return HttpResponseJson({
                'self' : full_url(request.path),
                self.collection.collection_name: items_list
                })

class ItemView(RestView):
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
            return HttpResponseNotFound(
                '%s not found' % self.collection.item_name.capitalize())
        return HttpResponseJson(item.attributes_dict())

    def delete(self, request, uuid):
        """Deletes a resource with a given uuid."""
        deleted = self.collection.delete_item(uuid)
        if not deleted:
            return HttpResponseNotFound(
                '%s not found' % self.collection.item_name.capitalize())
        return HttpResponseNoContent()

class OpenAccessView(RestView):
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
            return HttpResponseNotFound('Location not found.')
        if location.open_access:
            return HttpResponseJson(self._attributes_dict(request))

        location.grant_open_access()
        response =  HttpResponseCreated(self._attributes_dict(request))
        response['Location'] = full_url(request.path)
        return response

    def get(self, request, location_uuid):
        """Check if a resource that enables open access to a location exists."""
        location = self.locations_collection.find_item(location_uuid)
        if location is None:
            return HttpResponseNotFound('Location not found.')
        if location.open_access is False:
            return HttpResponseNotFound(
                'Open access to location disallowed.')
        return HttpResponseJson(self._attributes_dict(request))

    def delete(self, request, location_uuid):
        """Deletes a resource.

        Disables open access to a given location.
        """
        location = self.locations_collection.find_item(location_uuid)
        if location is None:
            return HttpResponseNotFound('Location not found.')
        if location.open_access is False:
            return HttpResponseNotFound(
                'Open access to location already disallowed.')
        location.revoke_open_access()
        return HttpResponseNoContent()

class AllowedUsersView(RestView):
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
            return HttpResponseNotFound('Location not found.')
        try:
            (permission, created) = location.grant_access(user_uuid)
            attributes_dict = permission.attributes_dict()
            if created:
                response =  HttpResponseCreated(attributes_dict)
                response['Location'] = attributes_dict['self']
            else:
                response = HttpResponseJson(attributes_dict)
            return response
        except LookupError as ex:
            return HttpResponseNotFound(ex)

    def get(self, request, location_uuid, user_uuid):
        """Checks if a resource that grants access exists.

        This is not equivalent of checking if the user can access the
        location. If the location is open, but the user is not
        explicitly granted access, not found failure is returned.
        """
        location = self.locations_collection.find_item(location_uuid)
        if location is None:
            return HttpResponseNotFound('Location not found.')
        try:
            permission = location.get_permission(user_uuid)
            return HttpResponseJson(permission.attributes_dict())
        except LookupError as ex:
            return HttpResponseNotFound(ex)

    def delete(self, request, location_uuid, user_uuid):
        """Deletes a resource

        Revokes access to a given location by a given user. If the
        location is open, the user will still be able to access the
        location after this call succeeds.
        """
        location = self.locations_collection.find_item(location_uuid)
        if not location:
            return HttpResponseNotFound('Location not found.')
        try:
            location.revoke_access(user_uuid)
            return HttpResponseNoContent()
        except LookupError as ex:
            return HttpResponseNotFound(ex)
