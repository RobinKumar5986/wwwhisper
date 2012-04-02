# Create your views here.

from django.conf import settings
from django.contrib.auth.models import User
from django.views.generic import View
from django.core import serializers
from django.http import HttpResponse
from auth.models import HttpResource
from auth.models import HttpPermission
from functools import wraps
from urlparse import urlparse

import json
import string
import re
import urllib
import posixpath
#TODO: style guide. Cammel names or names with '_'?

#TODO: acladmin ->admin?

def getAllowedUsersList(resourcePath):
    return [permission.user.email for permission in
            HttpPermission.objects.filter(http_resource = resourcePath)]

def getResourceList():
    return [ {
            'path': resource.path,
            'allowedUsers': getAllowedUsersList(resource.path)
            } for resource in HttpResource.objects.all()]

def onResourceList(path_arg):
    return HttpResource.objects.filter(path = path_arg).count() > 0

# Rename (user not contact)
def getContactList():
    return [user.email for user in User.objects.all()]

def onContactList(email_arg):
    return User.objects.filter(email = email_arg).count() > 0

def can_access(email, path):
    return HttpPermission.objects.filter(
        http_resource = path, user__email = email).count() > 0

def model2json(csrf_token):
    site_url = getattr(settings, 'SITE_URL',
                       'WARNING: SITE_URL is not set')
    return json.dumps({
            'resourcesRoot': site_url,
            'csrfToken': csrf_token,
            'resources': getResourceList(),
            'contacts': getContactList()
            })

def success(message=None):
    if message:
        return HttpResponse(message, status=200)
    return HttpResponse(status=200)


def error(message):
    # TODO: change status.
    return HttpResponse(message, status=400)

def methodNotAllowed():
    return HttpResponse(status=405)

def csrf_token_valid(token, session_key):
    return token == session_key

def email_valid(email):
    """Validates email with regexp defined by BrowserId:
    browserid/static/dialog/resources/validation.js
    """
    return re.match(
        "^[\w.!#$%&'*+\-/=?\^`{|}~]+@[a-z0-9-]+(\.[a-z0-9-]+)+$",
        email) != None;

#TODO: make these 3 symetric
def validate_path(path):
    parsed_url = urlparse(path)
    not_expected = []
    if parsed_url.scheme != '':
        not_expected.append("scheme: '%s'" % parsed_url.scheme)
    if parsed_url.netloc != '':
        not_expected.append("domain: '%s'" % parsed_url.netloc)
    if parsed_url.params != '':
        not_expected.append("parameters: '%s'" % parsed_url.params)
    if parsed_url.query != '':
        not_expected.append("query: '%s'" % parsed_url.query)
    if parsed_url.fragment != '':
        not_expected.append("fragment: '%s'" % parsed_url.fragment)
    if parsed_url.port != None:
        not_expected.append("port: '%d'" % parsed_url.port)
    if parsed_url.username != None:
        not_expected.append("username: '%s'" % parsed_url.username)
    if len(not_expected):
        return (False, "Invalid path. Specify only a path to a resource " \
                    "without %s" % string.join(not_expected, ", "))
    path = parsed_url.path.strip()
    if path == '':
        return (False, 'Empty path.')
    if posixpath.normpath(path) != path:
        return (False, "Path '%s' should be normalized " \
                    "(without .., /./, //)" % path)
    #TODO: test if this makes sense at all.
    try:
        path = path.encode('utf-8', 'strict')
    except UnicodeError, er:
        return (False, 'Invalid encoding of path %s' % str(er))
    return (True, urllib.quote(path, '/~'))

class Model(View):
    def get(self, request):
        print "FIUUUUUUUUU"
        data = model2json(request.session.session_key)
        print "FFFFIUUUU2 " + str(data) + " session: " \
            + request.session.session_key
        return HttpResponse(data, mimetype="application/json")

class RestView(View):
    def dispatch(self, request):
        request_args = json.loads(request.raw_post_data)
        csrf_token = request_args.pop('csrfToken', None)
        if csrf_token == None:
            return error('CSRF protection token missing')
        if not csrf_token_valid(csrf_token, request.session.session_key):
            return error('Invalid CSRF protection token')

        if request.method.lower() in self.http_method_names:
            handler = getattr(
                self, request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed

        # TODO: maybe do not pass request?
        return handler(request, **request_args)

class Resource(RestView):
    def put(self, request, path):
        print "Add resource " + path
        (is_correct, result) = validate_path(path)
        if not is_correct:
            return error(result)
        if onResourceList(result):
            return error(result + ' already exists')
        HttpResource(path = result).save()
        # TODO: should each put return result for symetry?
        # TODO: should this be returned as json object?
        return success(result)

    def delete(self, request, path):
        print "Remove resource " + path
        r = HttpResource.objects.filter(path = path)
        if r.count() == 0:
            return error(path + ' does not exist')
        r.delete()
        return success()

class Contact(RestView):
    def put(self, request, email):
        print "Add contact " + email
        if onContactList(email):
            return error(email + ' already on contact list')
        if not email_valid(email):
            return error('Invalid email format')
        user = User.objects.create_user(email, email)
        user.is_active = True
        user.save()
        return success()

    def delete(self, request, email):
        print "Remove contact " + email
        u = User.objects.filter(email = email)
        if u.count() == 0:
            return error(email + ' is not on contact list')
        u.delete()
        return success()

class Permission(RestView):
    def put(self, request, email, path):
        print "Grant permission to " + path + " for " + email
        if not onContactList(email):
            return error('Unknown user ' + email)
        if not onResourceList(path):
            return error('Resource does not exist ' + path)
        if can_access(email, path):
            return error(email + ' already can access ' + path)
        user_id = User.objects.get(email=email).id
        HttpPermission.objects.create(
            http_resource_id = path, user_id = user_id).save()
        return success()

    def delete(self, request, email, path):
        print "Revoke permission to " + path + " for " + email
        p = HttpPermission.objects.filter(
            user__email = email, http_resource = path);
        if p.count() == 0:
            return error(email + ' can not access ' + path)
        p.delete()
        return success()

