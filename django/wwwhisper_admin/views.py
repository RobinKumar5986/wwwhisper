from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.views.decorators.cache import cache_control

from wwwhisper_auth.http import HttpResponseBadRequest
from wwwhisper_auth.http import HttpResponseCreated
from wwwhisper_auth.http import HttpResponseNoContent
from wwwhisper_auth.http import RestView
from wwwhisper_auth.models import CreationException
from wwwhisper_auth.models import full_url

import json
import logging
import uuid

logger = logging.getLogger(__name__)

class CollectionView(RestView):
    collection = None

    def post(self, request, **kwargs):
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
        items_list = [item.attributes_dict() for item in self.collection.all()]
        data = json.dumps({
                'self' : full_url(request.path),
                self.collection.collection_name: items_list
                })
        return HttpResponse(data, mimetype="application/json")

    def _item_path(self, collection_url, uuid):
        return collection_url + uuid + "/"

class ItemView(RestView):
    collection = None

    def get(self, request, **kwargs):
        item = self.collection.find_item(**kwargs)
        if item is None:
            return HttpResponseNotFound(
                '%s not found' % self.collection.item_name.capitalize())
        return HttpResponse(json.dumps(item.attributes_dict()),
                            mimetype="application/json")

    def delete(self, request, **kwargs):
        deleted = self.collection.delete_item(**kwargs)
        if not deleted:
            return HttpResponseNotFound(
                '%s not found' % self.collection.item_name.capitalize())
        return HttpResponseNoContent()

class OpenAccessView(RestView):
    locations_collection = None

    @staticmethod
    def _attributes_dict(request):
        return {'self' : full_url(request.path)}

    # TODO: Move json serialization to http module.
    @staticmethod
    def _json_representation(request):
        return json.dumps(OpenAccessView._attributes_dict(request))

    def get(self, request, location_uuid):
        location = self.locations_collection.find_item(location_uuid)
        if location is None:
            return HttpResponseNotFound('Location not found.')
        if location.open_access is False:
            return HttpResponseNotFound(
                'Open access to location disallowed.')
        return HttpResponse(self._json_representation(request),
                            mimetype="application/json")

    def put(self, request, location_uuid):
        location = self.locations_collection.find_item(location_uuid)
        if location is None:
            return HttpResponseNotFound('Location not found.')
        if location.open_access:
            return HttpResponse(self._json_representation(request),
                                mimetype="application/json")
        location.grant_open_access()
        response =  HttpResponseCreated(self._attributes_dict(request))
        response['Location'] = full_url(request.path)
        return response

    def delete(self, request, location_uuid):
        location = self.locations_collection.find_item(location_uuid)
        if location is None:
            return HttpResponseNotFound('Location not found.')
        if location.open_access is False:
            return HttpResponseNotFound(
                'Open access to location already disallowed.')
        location.revoke_open_access()
        return HttpResponseNoContent()

class AllowedUsersView(RestView):
    locations_collection = None

    def get(self, request, location_uuid, user_uuid):
        location = self.locations_collection.find_item(location_uuid)
        if location is None:
            return HttpResponseNotFound('Location not found.')
        try:
            permission = location.get_permission(user_uuid)
            return HttpResponse(json.dumps(permission.attributes_dict()),
                                mimetype="application/json")
        except LookupError, ex:
            return HttpResponseNotFound(ex)

    def delete(self, request, location_uuid, user_uuid):
        location = self.locations_collection.find_item(location_uuid)
        if not location:
            return HttpResponseNotFound('Location not found.')
        try:
            location.revoke_access(user_uuid)
            return HttpResponseNoContent()
        except LookupError, ex:
            return HttpResponseNotFound(ex)


    def put(self, request, location_uuid, user_uuid):
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
                response = HttpResponse(json.dumps(attributes_dict),
                                        mimetype="application/json")
            return response
        except LookupError, ex:
            return HttpResponseNotFound(ex)
