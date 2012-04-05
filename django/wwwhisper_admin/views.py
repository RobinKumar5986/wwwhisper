from django.conf import settings
from django.contrib.auth.models import User
from django.core import serializers
from django.http import HttpResponse
from wwwhisper_auth.rest_view import RestView

import wwwhisper_auth.acl as acl
import json
import logging

logger = logging.getLogger(__name__)

#TODO: acladmin ->admin?

def success(message=None):
    if message:
        return HttpResponse(message, status=200)
    return HttpResponse(status=200)

def error(message):
    logger.debug('error %s' % (message))
    return HttpResponse(message, status=400)


def model2json():
    site_url = getattr(settings, 'SITE_URL',
                       'WARNING: SITE_URL is not set')
    return json.dumps({
            'locationsRoot': site_url,
            'locations': [ {
                    'path': path,
                    'allowedUsers': acl.allowed_emails(path)
                    } for path in acl.locations()],
            'contacts': acl.emails()
            })

class Model(RestView):
    def get(self, request):
        data = model2json()
        return HttpResponse(data, mimetype="application/json")

# TODO: rename resource -> location
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

# TODO rename contact
class Contact(RestView):
    def put(self, request, email):
        if not acl.is_email_valid(email):
            return error('Invalid email format.')
        user_added = acl.add_user(email)
        if not user_added:
            return error('Email already on contact list.')
        return success()

    def delete(self, request, email):
        user_deleted = acl.del_user(email)
        if not user_deleted:
            return error('Email is not on contact list.')
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

