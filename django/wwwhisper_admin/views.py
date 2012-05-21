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
# TODO: remove duplication
def site_url():
    return getattr(settings, 'SITE_URL',
                   'WARNING: SITE_URL is not set')

# TODO: remove duplication
# TODO: should HttpRequest.build_absolute_uri(request.path) be used instead?
def full_url(absolute_path):
    return site_url() + absolute_path

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

class CollectionView(RestView):
    collection = None

    def post(self, request, **kwargs):
        try:
            created_item = self.collection.create_item(**kwargs)
        except CreationException, ex:
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

class GrantAccessView(RestView):
    locations_collection = None

    def put(self, request, location_uuid, userid):
        # TODO: check if urn is correct.
        user_uuid = userid.replace('urn:uuid:', '')
        location = self.locations_collection.get(location_uuid)
        if not location:
            return HttpResponseNotFound('Location not found')
        try:
            location.grant_access(user_uuid)
        except LookupError, ex:
            # User not found.
            return HttpResponseNotFound(ex)
        return HttpResponseNoContent()

class Permission(RestView):

    def delete(self, request, email, path):
        access_revoked = acl.revoke_access(email, path)
        if not access_revoked:
            return error('User can not access location.')
        return success()

