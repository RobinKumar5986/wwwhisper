from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.forms import ValidationError
from urlparse import urlparse

import posixpath
import re
import string
import sys
import uuid

SITE_URL = getattr(settings, 'SITE_URL', None)
if SITE_URL is None:
    raise ImproperlyConfigured(
        'WWWhisper requires SITE_URL to be set in django settings.py file');

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
    not_authenticated_access = models.BooleanField(default=False, null=False)

    def allow_not_authenticated_access(self):
        self.not_authenticated_access = True;
        self.save();

    def disallow_not_authenticated_access(self):
        self.not_authenticated_access= False
        self.save();

    def can_access(self, user_uuid):
        return (self.not_authenticated_access
                or _find(Permission,
                         user__username=user_uuid,
                         http_location=self.path) is not None)

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
        validation_error = validate_path(path)
        if validation_error is not None:
            raise CreationException(validation_error)
        validation_error = _find_query_params_or_fragment(path)
        if validation_error is not None:
            raise CreationException(validation_error)
        if _find(Location, path=path) is not None:
            raise CreationException('Location already exists.')
        location = Location.objects.create(path=path)
        location.save()
        return location


    def find_parent(self, normalized_path):
        normalized_path_len = len(normalized_path)
        longest_matched_location = None
        longest_matched_location_len = -1

        for location in Location.objects.all():
            probed_path = location.path
            probed_path_len = len(probed_path)
            trailing_slash_index = None
            if probed_path[probed_path_len - 1] == '/':
                trailing_slash_index = probed_path_len - 1
            else:
                trailing_slash_index = probed_path_len

            if (normalized_path.startswith(probed_path) and
                probed_path_len > longest_matched_location_len and
                (probed_path_len == normalized_path_len or
                 normalized_path[trailing_slash_index] == '/')) :
                longest_matched_location_len = probed_path_len
                longest_matched_location = location
        return longest_matched_location

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

def validate_path(path):
    if path == '':
        return 'Path should not be empty.'
    elif not posixpath.isabs(path):
        return 'Path should be absolute (starting with /).'
    normalized_path =  posixpath.normpath(path)
    if (normalized_path != path and
        normalized_path + '/' != path):
        return 'Path should be normalized (without /../ or /./ or //)'
    return None

def _find_query_params_or_fragment(absolute_path):
    parsed_url = urlparse(absolute_path)
    not_expected = []
    if parsed_url.params != '':
        not_expected.append("parameters: '%s'" % parsed_url.params)
    if parsed_url.query != '':
        not_expected.append("query: '%s'" % parsed_url.query)
    if parsed_url.fragment != '':
        not_expected.append("fragment: '%s'" % parsed_url.fragment)

    if len(not_expected):
        return 'Invalid path, not expected: %s.' % \
            string.join(not_expected, ', ')
    return None

