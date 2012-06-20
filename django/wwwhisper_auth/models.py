"""Data model fot the access control mechanism.

Stores information about locations, users and permissions. Provides
methods that map to REST operations that can be performed on users,
locations and permissions resources. Allows to retrieve externally
visible attributes of these resources, the attributes are returned as
a resource representation by REST methods.

Resources are identified by an externally visible UUIDs. Standard
primary key ids are not used for external identification purposes,
because those ids can be reused after object is deleted.

Makes sure entered emails and paths are valid.
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.forms import ValidationError
from wwwhisper_auth import  url_path

import re
import uuid as uuidgen

# TODO: Fix lint warning also for django-lint.

SITE_URL = getattr(settings, 'SITE_URL', None)
if SITE_URL is None:
    raise ImproperlyConfigured(
        'WWWhisper requires SITE_URL to be set in django settings.py file')

class CreationException(Exception):
    """Raised when creation of a resource failed."""
    pass

class ValidatedModel(models.Model):
    """Base class for all model classes.

    Makes sure all constraints are preserved before changed data is
    saved.
    """

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(ValidatedModel, self).save(*args, **kwargs)

    class Meta:
        """Disables creation of a DB table for ValidatedModel."""
        abstract = True

# Because Django authentication mechanism is used, users need to be
# represented by a standard Django User class. But some additions are
# needed:

"""Externally visible UUID of a user.

Allows to identify a REST resource representing a user. UUID is stored
in the username field when User object is created.
"""
User.uuid = property(lambda(self): self.username)

# TODO: Check if a doc string can be dynamically added.
"""Returns externally visible attributes of the user resource."""
User.attributes_dict = lambda(self): \
    _add_common_attributes(self, {'email': self.email})

class Location(ValidatedModel):
    """A location for which access control rules are defined.

    Location is uniquely identified by its canonical path. All access
    control rules defined for a location apply also to sub-paths,
    unless a more specific location exists. In such case the more
    specific location takes precedence over the more generic one.

    For example, if a location with a path /pub is defined and a user
    foo@example.com is granted access to this location, the user can
    access /pub and all sub path of /pub. But if a location with a
    path /pub/beer is added, and the user foo@example.com is not
    granted access to this location, the user won't be able to access
    /pub/beer and all its sub-paths.

    Attributes:
      path: Canonical path of the location.
      uuid: Externally visible UUID of the location, allows to identify a REST
          resource representing the location.
      open_access: If true, access to the location does not require
          authentication.
    """

    path = models.CharField(max_length=2000, null=False, primary_key=True)
    uuid = models.CharField(max_length=36, null=False, db_index=True,
                            editable=False)
    open_access = models.BooleanField(default=False, null=False)

    def grant_open_access(self):
        """Allows access to the location without authentication.

        For authenticated users, access is also always allowed.
        """
        self.open_access = True
        self.save()

    def revoke_open_access(self):
        """Disallows not-authenticated access to the location."""
        self.open_access = False
        self.save()

    def can_access(self, user_uuid):
        """Determines if a user can access the location.

        Args:
            user_uuid: string UUID of a user.

        Returns:
            True if the user is granted permission to access the
            location or it the location is open.
        """
        return (self.open_access
                or _find(Permission,
                         user__username=user_uuid,
                         http_location=self.path) is not None)

    def grant_access(self, user_uuid):
        """Grants access to the location to a given user.

        Args:
            user_uuid: string UUID of a user.

        Returns:
            (new Permission object, True) if access to the location was
                successfully granted.
            (existing Permission object, False) if user already had
                granted access to the location.

        Raises:
            LookupError: No user with a given UUID.
        """
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
        """Revokes access to the location from a given user.

        Args:
            user_uuid: string UUID of a user.

        Raises:
            LookupError: No user with a given UUID or the user can not
                access the location.
        """
        permission = self.get_permission(user_uuid)
        permission.delete()

    def get_permission(self, user_uuid):
        """Gets Permission object for a given user.

        Args:
            user_uuid: string UUID of a user.

        Raises:
            LookupError: No user with a given UUID or the user can not
                access the location.
        """
        user = _find(User, username=user_uuid)
        if user is None:
            raise LookupError('User not found.')
        permission = _find(
            Permission, http_location_id=self.path, user_id=user.id)
        if permission is None:
            raise LookupError('User can not access location.')
        return permission

    def allowed_users(self):
        """"Returns a list of users that can access the location."""
        return [permission.user for permission in
                Permission.objects.filter(http_location=self.path)]

    def attributes_dict(self):
        """Returns externally visible attributes of the location resource."""
        return _add_common_attributes(self, {
                'path': self.path,
                'openAccess': self.open_access,
                'allowedUsers': [
                    user.attributes_dict() for user in self.allowed_users()
                    ],
                })

    @models.permalink
    def get_absolute_url(self):
        """Constructs URL of the location resource."""
        return ('wwwhisper_location', (), {'uuid' : self.uuid})

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = str(uuidgen.uuid4())
        return super(Location, self).save(*args, **kwargs)

    def __unicode__(self):
        return "%s" % (self.path)

class Permission(ValidatedModel):
    """Connects a location with a user that can access the location.

    Attributes:
        http_location: The location to which the Permission object gives access.
        user: The user that is given access to the location.
    """

    http_location = models.ForeignKey(Location)
    user = models.ForeignKey(User)

    def attributes_dict(self):
        """Returns externally visible attributes of the permission resource."""
        return _add_common_attributes(
            self, {'user': self.user.attributes_dict()})

    @models.permalink
    def get_absolute_url(self):
        """Constructs URL of the permission resource."""
        return ('wwwhisper_allowed_user', (),
                {'location_uuid' : self.http_location.uuid,
                 'user_uuid': self.user.uuid})

    def __unicode__(self):
        return "%s, %s" % (self.http_location, self.user.email)

class Collection(object):
    """A common base class for managing a collection of resources.

    Resources in the collection are of the same type and need to be
    identified by an UUID.

    Attributes (Need to be defined in subclasses):
        item_name: Name of a resource stored in the collection.
        model_class: Class that manages storage of resources.
        uuid_column_name: Name of a column in the model class that stores
            a resource uuid.
    """

    def all(self):
        """Returns all items in the collection."""
        return self.model_class.objects.all()

    def find_item(self, uuid):
        """Finds an item with a given UUID.

        Returns:
           The item or None if not found.
        """
        filter_args = {self.uuid_column_name: uuid}
        return _find(self.model_class, **filter_args)

    def delete_item(self, uuid):
        """Deletes an item with a given UUID.

        Returns:
           True if the item existed and was deleted, False if not found.
        """
        item = self.find_item(uuid)
        if item is None:
            return False
        item.delete()
        return True

    @property
    def collection_name(self):
        return self.item_name + 's'

class UsersCollection(Collection):
    """Collection of users resources."""

    item_name = 'user'
    model_class = User
    uuid_column_name = 'username'

    def create_item(self, email):
        """Creates a new User object.

        Args:
            email: An email of the created user.

        Raises:
            CreationException if the email is invalid or if a user
            with such email already exists.
        """
        try:
            encoded_email = _encode_email(email)
        except ValidationError, ex:
            raise CreationException(ex)
        if _find(User, email=encoded_email) is not None:
            raise CreationException('User already exists.')
        user = User.objects.create(
            username=str(uuidgen.uuid4()), email=encoded_email, is_active=True)
        return user

    def find_item_by_email(self, email):
        """Finds a user with a given email.

        Returns:
            A User object or None if not found.
        """
        try:
            encoded_email = _encode_email(email)
        except ValidationError:
            return None
        return _find(self.model_class, email=encoded_email)

class LocationsCollection(Collection):
    """Collection of locations resources."""

    item_name = 'location'
    model_class = Location
    uuid_column_name = 'uuid'

    def create_item(self, path):
        """Creates a new Location object.

        The location path should be canonical and should not contain
        parts that are not used for access control (query, fragment,
        parameters).

        Args:
            path: A canonical path to the location.

        Raises:
            CreationException if the path is invalid or if a location
            with such path already exists.
        """

        if not url_path.is_canonical(path):
            raise CreationException(
                'Path should be absolute and normalized (starting with / '\
                    'without /../ or /./ or //).')
        if url_path.contains_fragment(path):
            raise CreationException(
                "Path should not contain fragment ('#' part).")
        if url_path.contains_query(path):
            raise CreationException(
                "Path should not contain query ('?' part).")
        if url_path.contains_params(path):
            raise CreationException(
                "Path should not contain parameters (';' part).")
        if _find(Location, path=path) is not None:
            raise CreationException('Location already exists.')
        location = Location.objects.create(path=path)
        location.save()
        return location


    def find_location(self, canonical_path):
        """Finds a location that defines access to a given path.

        Args:
            canonical_path: The path for which matching location is searched.

        Returns:
            The most specific location with path matching a given path or None
            if no matching location exists.
        """
        canonical_path_len = len(canonical_path)
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

            if (canonical_path.startswith(probed_path) and
                probed_path_len > longest_matched_location_len and
                (probed_path_len == canonical_path_len or
                 canonical_path[trailing_slash_index] == '/')) :
                longest_matched_location_len = probed_path_len
                longest_matched_location = location
        return longest_matched_location

def full_url(absolute_path):
    """Return full url of a resource with a given path."""
    return SITE_URL + absolute_path

def _urn_from_uuid(uuid):
    return 'urn:uuid:' + uuid

def _add_common_attributes(item, attributes_dict):
    """Inserts common attributes of an item to a given dict.

    Attributes that are common for different resource types are a
    'self' link and an 'id' field.
    """
    attributes_dict['self'] = full_url(item.get_absolute_url())
    if hasattr(item, 'uuid'):
        attributes_dict['id'] = _urn_from_uuid(item.uuid)
    return attributes_dict

def _find(model_class, **kwargs):
    """Finds a single item satisfying a given expression.

    Args:
        model_class: Model that manages stored items.
        **kwargs: Filtering expression, at most one element can satisfy it.
    Returns:
        An item that satisfies expression or None.
    """
    item = model_class.objects.filter(**kwargs)
    count = item.count()
    assert count <= 1
    if count == 0:
        return None
    return item.get()

def _encode_email(email):
    """Encodes and validates email address.

    Email is converted to a lower case not to require emails to be added
    to the access control list with the same capitalization that the
    user signs-in with.
    """
    encoded_email = email.lower()
    if not _is_email_valid(encoded_email):
        raise ValidationError('Invalid email format.')
    return encoded_email

def _is_email_valid(email):
    """Validates email with a regexp defined by BrowserId:
    browserid/browserid/static/dialog/resources/validation.js
    """
    return re.match(
        "^[\w.!#$%&'*+\-/=?\^`{|}~]+@[a-z0-9-]+(\.[a-z0-9-]+)+$",
        email) != None
