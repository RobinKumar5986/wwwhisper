from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from wwwhisper_auth.rest_view import RestView
from wwwhisper_auth.acl import CreationException

import wwwhisper_auth.acl as acl
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
def site_url():
    return getattr(settings, 'SITE_URL',
                   'WARNING: SITE_URL is not set')

def full_url(absolute_path):
    return site_url() + absolute_path

def urn_from_uuid(uuid):
    return 'urn:uuid:' + uuid

def model2json():
    site_url = getattr(settings, 'SITE_URL',
                       'WARNING: SITE_URL is not set')
    return json.dumps({
            'locationsRoot': site_url,
            'locations': [{
                    'path': path,
                    'allowedUsers': acl.allowed_emails(path)
                    } for path in acl.locations()],
            #'users': acl.emails()
            })

class Model(RestView):
    def get(self, request):
        data = model2json()
        return HttpResponse(data, mimetype="application/json")

def item_attributes(item, item_path):
    urn = urn_from_uuid(item.uuid)
    attributes_dict = {}
    attributes_dict['self'] = full_url(item_path)
    attributes_dict['id'] = urn
    attributes_dict.update(item.attributes_dict())
    return attributes_dict


class CollectionView(RestView):
    collection = None

    def post(self, request, **kwargs):
        try:
            created_item = self.collection.create_item(**kwargs)
        except CreationException, ex:
            return error(ex)
        attributes_dict = item_attributes(
            created_item, self._item_path(request.path, created_item.uuid))
        response = HttpResponse(json.dumps(attributes_dict),
                                mimetype="application/json",
                                status=201)
        response['Location'] = attributes_dict['self']
        response['Content-Location'] = attributes_dict['self']
        return response

    def get(self, request):
        items_list = [
            item_attributes(item, self._item_path(request.path, item.uuid))
            for item in self.collection.all()
            ]
        data = json.dumps({
                'self' : full_url(request.path),
                self.collection.collection_name: items_list
                })
        return HttpResponse(data, mimetype="application/json")

    def _item_path(self, collection_url, uuid):
        return collection_url + uuid + "/"

class ItemView(RestView):
    collection = None

    def get(self, request, uuid):
        item = self.collection.get(uuid)
        if item is None:
            return HttpResponseNotFound(
                '%s not found' % self.collection.item_name.capitalize())
        attributes_dict = item_attributes(item, request.path)
        return HttpResponse(json.dumps(attributes_dict),
                            mimetype="application/json")

    def delete(self, request, uuid):
        deleted = self.collection.delete(uuid)
        if not deleted:
            return HttpResponseNotFound(
                '%s not found' % self.collection.item_name.capitalize())
        return HttpResponseNoContent()


class Location(RestView):

    def delete(self, request, path):
        location_deleted = acl.del_location(path)
        if not location_deleted:
            return error('Location does not exist.')
        return success()

class Permission(RestView):
    def put(self, request, email, path):
        if not acl.grant_access(email, path):
            return error('User already can access location.')
        return success()

    def delete(self, request, email, path):
        access_revoked = acl.revoke_access(email, path)
        if not access_revoked:
            return error('User can not access location.')
        return success()

