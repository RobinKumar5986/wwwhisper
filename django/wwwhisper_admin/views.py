from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from wwwhisper_auth.rest_view import RestView

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

from django.contrib.auth.models import User as ModelUser

def user_dict(user):
    return {
        'self': full_url(user.get_absolute_url()),
        'email': user.email,
        'id': urn_from_uuid(user.username),
        }

def users_list():
    return [user_dict(user) for user in ModelUser.objects.all()]

class UserCollection(RestView):
    def post(self, request, email):
        if not acl.is_email_valid(email):
            return error('Invalid email format.')
        if acl.find_user(email):
            return error('User already exists.')
        user = ModelUser.objects.create(
            username=str(uuid.uuid4()), email=email, is_active=True)
        user_info = user_dict(user)
        response = HttpResponse(json.dumps(user_info),
                                mimetype="application/json",
                                status=201)
        response['Location'] = user_info['self']
        response['Content-Location'] = user_info['self']
        return response

    def get(self, request):
        data = json.dumps({
                'self' : full_url(request.path),
                'users': users_list()
                })
        return HttpResponse(data, mimetype="application/json")

class User(RestView):
    def get(self, request, uuid):
        query_set = ModelUser.objects.filter(username=uuid)
        assert query_set.count() <= 1
        if query_set.count() == 0:
            return HttpResponseNotFound('TODO: error message')
        user_info = user_dict(query_set.get())
        return HttpResponse(json.dumps(user_info),
                            mimetype="application/json")

    def delete(self, request, uuid):
        query_set = ModelUser.objects.filter(username=uuid)
        assert query_set.count() <= 1
        if query_set.count() == 0:
            return HttpResponseNotFound('TODO: error message')
        query_set.delete()
        return HttpResponseNoContent()

# Addlocation, deletelocation?
class Location(RestView):
    def put(self, request, path):
        try:
            result = acl.encode_path(path)
        except acl.InvalidPath, ex:
            return error('Invalid path ' + str(ex))
        location_added = acl.add_location(result)
        if not location_added:
            return error('Location already exists.')
        # TODO: should each put return result for symetry?
        # TODO: should this be returned as json object?
        return success(result)

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

