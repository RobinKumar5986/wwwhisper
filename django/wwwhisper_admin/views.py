from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from wwwhisper_auth.rest_view import RestView
from wwwhisper_auth.models import CreationException

import json
import logging
import uuid

logger = logging.getLogger(__name__)

class HttpResponseNoContent(HttpResponse):
    def __init__(self):
        super(HttpResponseNoContent, self).__init__(status=204)

def success(message=None):
    if message:
        return HttpResponse(message, status=200)
    return HttpResponse(status=200)

def error(message):
    logger.debug('Error %s' % (message))
    return HttpResponse(message, status=400)

# TODO: can this warning be fatal initialization error?
# TODO: remove duplication
def site_url():
    return getattr(settings, 'SITE_URL',
                   'WARNING: SITE_URL is not set')

# TODO: remove duplication
# TODO: should HttpRequest.build_absolute_uri(request.path) be used instead?
def full_url(absolute_path):
    return site_url() + absolute_path

class CollectionView(RestView):
    collection = None

    def post(self, request, **kwargs):
        try:
            created_item = self.collection.create_item(**kwargs)
        except CreationException as ex:
            return error(ex)
        attributes_dict = created_item.attributes_dict()
        response = HttpResponse(json.dumps(attributes_dict),
                                mimetype="application/json",
                                status=201)
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
        item = self.collection.get(**kwargs)
        if item is None:
            return HttpResponseNotFound(
                '%s not found' % self.collection.item_name.capitalize())
        return HttpResponse(json.dumps(item.attributes_dict()),
                            mimetype="application/json")

    def delete(self, request, **kwargs):
        deleted = self.collection.delete(**kwargs)
        if not deleted:
            return HttpResponseNotFound(
                '%s not found' % self.collection.item_name.capitalize())
        return HttpResponseNoContent()

class AllowedUsersView(RestView):
    locations_collection = None

    def get(self, request, location_uuid, user_uuid):
        location = self.locations_collection.get(location_uuid)
        if location is None:
            return HttpResponseNotFound('Location not found.')
        try:
            permission = location.get_permission(user_uuid)
            return HttpResponse(json.dumps(permission.attributes_dict()),
                                mimetype="application/json")
        except LookupError, ex:
            return HttpResponseNotFound(ex)

    def delete(self, request, location_uuid, user_uuid):
        location = self.locations_collection.get(location_uuid)
        if not location:
            return HttpResponseNotFound('Location not found.')
        try:
            location.revoke_access(user_uuid)
            return HttpResponseNoContent()
        except LookupError, ex:
            return HttpResponseNotFound(ex)


    def put(self, request, location_uuid, user_uuid):
        location = self.locations_collection.get(location_uuid)
        if not location:
            return HttpResponseNotFound('Location not found.')
        try:
            (permission, created) = location.grant_access(user_uuid)
            attributes_dict = permission.attributes_dict()
            if created:
                response =  HttpResponse(json.dumps(attributes_dict),
                                         mimetype="application/json",
                                         status=201)
                response['Location'] = attributes_dict['self']
            else:
                response = HttpResponse(json.dumps(attributes_dict),
                                        mimetype="application/json",
                                        status=200)
            return response
        except LookupError, ex:
            return HttpResponseNotFound(ex)
