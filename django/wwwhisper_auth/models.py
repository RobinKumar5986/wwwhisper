from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from urlparse import urlparse

import posixpath
import re
import string
import sys
import urllib
import uuid

# This attribute is required, exception is thrown when not set.
# TODO: raise ImproperlyConfigured().
SITE_URL = getattr(settings, 'SITE_URL')

class ValidationError(ValueError):
    pass

class CreationException(Exception):
    pass;

class ValidatedModel(models.Model):
    def save(self, *args, **kwargs):
        self.full_clean()
        return super(ValidatedModel, self).save(*args, **kwargs)

    class Meta:
        # Do not create a DB table for ValidatedModel.
        abstract = True

User.uuid = property(lambda(self): self.username)
User.attributes_dict = lambda(self): \
    _add_common_attributes(self, {'email': self.email})

class Location(ValidatedModel):
    path = models.CharField(max_length=2000, null=False, primary_key=True)
    uuid = models.CharField(max_length=36, null=False, db_index=True,
                            editable=False)
    def grant_access(self, user_uuid):
        user = _find(User, username=user_uuid)
        if user is None:
            raise LookupError('User not found')
        permission = _find(
            Permission, http_location_id=self.path, user_id=user.id)
        created = False
        if permission is None:
            created = True
            permission = Permission.objects.create(
                http_location_id=self.path, user_id=user.id)
            permission.save()
        return (permission, created)

    def revoke_access(self, user_uuid):
        permission = self.get_permission(user_uuid)
        permission.delete()


    def get_permission(self, user_uuid):
        user = _find(User, username=user_uuid)
        if user is None:
            raise LookupError('User not found.')
        permission = _find(
            Permission, http_location_id=self.path, user_id=user.id)
        if permission is None:
            raise LookupError('User can not access location.')
        return permission

    def allowed_users(self):
        return [permission.user.attributes_dict() for permission in
                Permission.objects.filter(http_location=self.path)]

    def attributes_dict(self):
        return _add_common_attributes(self, {
                'path': self.path,
                'allowedUsers': self.allowed_users(),
                })

    @models.permalink
    def get_absolute_url(self):
        return ('wwwhisper_location', (), {'uuid' : self.uuid})

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
        return super(Location, self).save(*args, **kwargs)

    def __unicode__(self):
        return "%s" % (self.path)

class Permission(ValidatedModel):
    http_location = models.ForeignKey(Location)
    user = models.ForeignKey(User)

    def attributes_dict(self):
        return _add_common_attributes(
            self, {'user': self.user.attributes_dict()})

    @models.permalink
    def get_absolute_url(self):
        return ('wwwhisper_allowed_user', (),
                {'location_uuid' : self.http_location.uuid,
                 'user_uuid': self.user.uuid})

    def __unicode__(self):
        return "%s, %s" % (self.http_location, self.user.email)

class Collection(object):
    def all(self):
        return self.model_class.objects.all()

    def find_item(self, uuid):
        filter_args = {self.uuid_column_name: uuid}
        return _find(self.model_class, **filter_args)

    def delete_item(self, uuid):
        item = self.find_item(uuid)
        if item is None:
            return False
        item.delete()
        return True

class UsersCollection(Collection):
    collection_name = 'users'
    item_name = 'user'
    model_class = User
    uuid_column_name = 'username'

    def create_item(self, email):
        try:
            encoded_email = _encode_email(email)
        except ValidationError, ex:
            raise CreationException(ex)
        if _find(User, email=encoded_email) is not None:
            raise CreationException('User already exists.')
        user = User.objects.create(
            username=str(uuid.uuid4()), email=encoded_email, is_active=True)
        return user

    def find_item_by_email(self, email):
        try:
            encoded_email = _encode_email(email)
        except ValidationError, ex:
            return None
        return _find(self.model_class, email=encoded_email);

class LocationsCollection(Collection):
    collection_name = 'locations'
    item_name = 'location'
    model_class = Location
    uuid_column_name = 'uuid'

    def create_item(self, path):
        try:
            encoded_path = _encode_path(path)
        except ValidationError, ex:
            raise CreationException(ex)
        if _find(Location, path=encoded_path) is not None:
            raise CreationException('Location already exists.')
        location = Location.objects.create(path=encoded_path)
        location.save()
        return location


# TODO: How to handle trailing '/'? Maybe remove it prior to adding path to db?
# TODO: change email to user id
def can_access(email, path):
    path_len = len(path)
    longest_match = ''
    longest_match_len = -1

    for location in Location.objects.all():
        probed_path = location.path
        probed_path_len = len(probed_path)
        stripped_probed_path = probed_path.rstrip('/')
        stripped_probed_path_len = len(stripped_probed_path)
        if (path.startswith(stripped_probed_path) and
            probed_path_len > longest_match_len and
            (stripped_probed_path_len == path_len
             or path[stripped_probed_path_len] == '/')):
            longest_match_len = probed_path_len
            longest_match = probed_path
    return longest_match_len != -1 \
        and  _find(Permission,
                   user__email=email,
                   http_location=longest_match) is not None

def full_url(absolute_path):
    return SITE_URL + absolute_path

def _urn_from_uuid(uuid):
    return 'urn:uuid:' + uuid

def _add_common_attributes(item, attributes_dict):
    attributes_dict['self'] = full_url(item.get_absolute_url())
    if hasattr(item, 'uuid'):
        attributes_dict['id'] = _urn_from_uuid(item.uuid)
    return attributes_dict

def _find(model_class, **kwargs):
    item = model_class.objects.filter(**kwargs)
    count = item.count()
    assert count <= 1
    if count == 0:
        return None
    return item.get()

def _encode_email(email):
    encoded_email = email.lower()
    if not _is_email_valid(encoded_email):
        raise ValidationError('Invalid email format.')
    return encoded_email

def _is_email_valid(email):
    """Validates email with regexp defined by BrowserId:
    browserid/browserid/static/dialog/resources/validation.js
    """
    return re.match(
        "^[\w.!#$%&'*+\-/=?\^`{|}~]+@[a-z0-9-]+(\.[a-z0-9-]+)+$",
        email) != None

def _encode_path(path):
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
        raise ValidationError('Invalid path, not expected: %s.'
                          % string.join(not_expected, ', '))
    stripped_path = parsed_url.path.strip()
    if stripped_path == '':
        raise ValidationError('Path should not be empty.')

    normalized_path =  posixpath.normpath(stripped_path)
    if (normalized_path != stripped_path and
        normalized_path + '/' != stripped_path):
        raise ValidationError(
            'Path should be normalized (without /../ or /./ or //)')
    #TODO: test if this makes sense:
    try:
        encoded_path = stripped_path.encode('utf-8', 'strict')
    except UnicodeError, er:
        raise ValidationError('Invalid path encoding %s' % str(er))
    return urllib.quote(encoded_path, '/~')

