from django.contrib.auth.models import User
from urlparse import urlparse
from wwwhisper_auth.models import HttpLocation
from wwwhisper_auth.models import HttpPermission

#import base64
#import hashlib
import posixpath
import re
import string
import urllib
import uuid

class InvalidPath(ValueError):
    pass

class CreationException(Exception):
    pass;


def _add(model_class, **kwargs):
    obj, created = model_class.objects.get_or_create(**kwargs)
    return created

def _del(model_class, **kwargs):
    object_to_del = model_class.objects.filter(**kwargs)
    assert object_to_del.count() <= 1
    if object_to_del.count() == 0:
        return False
    object_to_del.delete()
    return True

def _find(model_class, **kwargs):
    count = model_class.objects.filter(**kwargs).count()
    assert count <= 1
    return count > 0

def _all(model_class, field):
    return [obj.__dict__[field] for obj in model_class.objects.all()]

def add_location(path):
    return _add(HttpLocation, path=path)

def del_location(path):
    return _del(HttpLocation, path=path)

def find_location(path):
    return _find(HttpLocation, path=path)

def locations():
    return _all(HttpLocation, 'path')

def encode_path(path):
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
        raise InvalidPath('Invalid path, not expected: %s.'
                          % string.join(not_expected, ', '))
    stripped_path = parsed_url.path.strip()
    if stripped_path == '':
        raise InvalidPath('Path should not be empty.')

    normalized_path =  posixpath.normpath(stripped_path)
    if (normalized_path != stripped_path and
        normalized_path + '/' != stripped_path):
        raise InvalidPath(
            "Path should be normalized (without /../ or /./ or //)")
    #TODO: test if this makes sense:
    try:
        encoded_path = stripped_path.encode('utf-8', 'strict')
    except UnicodeError, er:
        raise InvalidPath('Invalid path encoding %s' % str(er))
    return urllib.quote(encoded_path, '/~')

def emails():
    return _all(User, 'email')

def grant_access(email, location_path):
    if not find_location(location_path):
        raise LookupError('Location does not exist')
    add_user(email)
    user_id = User.objects.get(email=email).id
    return _add(HttpPermission, http_location_id=location_path, user_id=user_id)

def revoke_access(email, location_path):
    if not find_location(location_path):
        raise LookupError('Location does not exist')
    return _del(HttpPermission, user__email=email, http_location=location_path)

# TODO: should this work only for defined locations or check parent locations?
def allowed_emails(path):
    return [permission.user.email for permission in
            HttpPermission.objects.filter(http_location=path)]

# TODO: How to handle trailing '/'? Maybe remove it prior to adding path to db?
def can_access(email, path):
    path_len = len(path)
    longest_match = ''
    longest_match_len = -1

    for probed_path in locations():
        probed_path_len = len(probed_path)
        stripped_probed_path = probed_path.rstrip('/')
        stripped_probed_path_len = len(stripped_probed_path)
        if (path.startswith(stripped_probed_path) and
            probed_path_len > longest_match_len and
            (stripped_probed_path_len == path_len
             or path[stripped_probed_path_len] == '/')):
            longest_match_len = probed_path_len
            longest_match = probed_path
    return longest_match_len != -1 and \
        _find(HttpPermission, user__email=email, http_location=longest_match)

def add_user(email):
    if find_user(email):
        return False
    User.objects.create(username=uuid.uuid4(), email=email, is_active=True)
    return True;

def del_user(email):
    return _del(User, email=email)

def find_user(email):
    return _find(User, email=email)

# def find_user_with_uuid(uid):
#     return _find(User, uid=uid)

# TODO: capital letters in email are not accepted
def is_email_valid(email):
    """Validates email with regexp defined by BrowserId:
    browserid/browserid/static/dialog/resources/validation.js
    """
    return re.match(
        "^[\w.!#$%&'*+\-/=?\^`{|}~]+@[a-z0-9-]+(\.[a-z0-9-]+)+$",
        email) != None

class UserCollection(object):
    collection_name = 'users'
    item_name = 'user'

    def create_item(self, email):
        if not is_email_valid(email):
            raise CreationException('Invalid email format.')
        if find_user(email):
            raise CreationException('User already exists.')
        return User.objects.create(
            username=str(uuid.uuid4()), email=email)

    def all(self):
        return User.objects.all()

    def get(self, uuid):
        item = User.objects.filter(username=uuid)
        assert item.count() <= 1
        if item.count() == 0:
            return None
        return item.get()

    def delete(self, uuid):
        return _del(User, username=uuid)


class LocationCollection(object):
    collection_name = 'locations'
    item_name = 'location'

    def create_item(self, path):
        try:
            encoded_path = encode_path(path)
        except InvalidPath, ex:
            raise CreationException('Invalid path ' + str(ex))
        if find_location(encoded_path):
            raise CreationException('Location already exists.')
        return HttpLocation.objects.create(path=path)

    def all(self):
        return Location.objects.all()

    def get(self, uuid):
        item = HttpLocation.objects.filter(uuid=uuid)
        assert item.count() <= 1
        if item.count() == 0:
            return None
        return item.get()

    def delete(self, uuid):
        return _del(HttpLocation, uuid=uuid)
