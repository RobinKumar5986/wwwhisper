# wwwhisper - web access control.
# Copyright (C) 2012, 2013 Jan Wrobel <wrr@mixedbit.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Data model for the access control mechanism.

Stores information about sites, locations, users and permissions. A
site has users, locations (paths) and permissions - rules that define
which user can access which locations. Sites are isolated. Users and
locations are associated with a single site and are used only for this
site.

Provides methods that map to REST operations that can be performed on
users, locations and permissions resources. Allows to retrieve
externally visible attributes of these resources, the attributes are
returned as a resource representation by REST methods.

Resources are identified by an externally visible UUIDs. Standard
primary key ids are not used for external identification purposes,
because those ids can be reused after object is deleted.

Makes sure entered emails and paths are valid.
"""

from django.contrib.auth.models import User
from django.db import models
from django.db.models import F # TODO: remove.
from django.db.models import signals
from django.forms import ValidationError
from functools import wraps
from wwwhisper_auth import  url_path

import re
import uuid as uuidgen
import random

USERNAME_LEN=7
assert USERNAME_LEN <= User._meta.get_field('username').max_length

class ValidatedModel(models.Model):
    """Base class for all model classes.

    Makes sure all constraints are preserved before changed data is
    saved.
    """

    class Meta:
        """Disables creation of a DB table for ValidatedModel."""
        abstract = True

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(ValidatedModel, self).save(*args, **kwargs)

class Site(ValidatedModel):
    """A site to which access is protected.

    Site has locations and users.

    Attributes:
      site_id: Can be a domain or any other string.
      #mod_id: Changed after any modification of the site data. Allows
      #    to determine when caches need to be updated
    """
    __MAX_MOD_ID = 2000000000
    site_id = models.TextField(primary_key=True, db_index=True, editable=False)
    mod_id = models.IntegerField(default=0)

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)

    def lazy_init(self):
        self.locations = LocationsCollection(self)
        self.users = UsersCollection(self)
        self.locations = LocationsCollection(self)

    def site_modified(self):
        # TODO: do all updates within a transaction.
        self.mod_id = (self.mod_id + 1) % self.__MAX_MOD_ID
        self.save()

#TODO: document caching mechanism.
site_cache = {}

def create_site(site_id):
    """Creates a new Site object.

    Args:
       site_id: A domain or other id of the created site.
    Raises:
       ValidationError if a site with such id already exists.
    """
    site =  Site.objects.create(site_id=site_id)
    site.lazy_init()
    site_cache[site_id] = site
    return site

def find_site(site_id):
    site = _find(Site, site_id=site_id)
    if site is None:
        site_cache.pop(site_id, None)
        return None
    cached_site = site_cache.get(site_id, None)
    if (cached_site is not None and
        cached_site.mod_id == site.mod_id):
        return cached_site
    site.lazy_init()
    site_cache[site_id] = site
    return site

def delete_site(site_id):
    site_cache.pop(site_id, None)
    site = find_site(site_id)
    if site is None:
        return False
    # Users need to be deleted manually, because User object does not
    # have a foreign key to the Site (unlike UserExtras and
    # Locations).
    map(lambda user: user.delete(), site.users.all())
    site.delete()
    return True

def modify_site(decorated_method):
    @wraps(decorated_method)
    def wrapper(self, *args, **kwargs):
        result = decorated_method(self, *args, **kwargs)
        # If no exception.
        self.site.site_modified()
        return result
    return wrapper

def check_cache(decorated_method):
    @wraps(decorated_method)
    def wrapper(self, *args, **kwargs):
        if self.site.mod_id != self.cache_mod_id:
            self.update_cache()
        return decorated_method(self, *args, **kwargs)
    return wrapper


# Because Django authentication mechanism is used, users need to be
# represented by a standard Django User class. But some additions are
# needed:

class UserExtras(models.Model):
    """Extends User model to store site to which user object belongs."""

    user = models.OneToOneField(User)
    site = models.ForeignKey(Site, related_name='+')
    # Preferably uuid would be stored in username, but Django limits
    # the length of the username field to 30 chars.
    uuid = models.CharField(max_length=36, db_index=True,
                            editable=False, unique=True)

def user_uuid(self):
    if hasattr(self, '_cached_uuid'):
        return self._cached_uuid
    self._cached_uuid = self.get_profile().uuid
    return self._cached_uuid

User.uuid = property(fget=user_uuid, doc=\
"""Externally visible UUID of a user.

Allows to identify a REST resource representing a user.
""")

User.attributes_dict = lambda self, site_url: \
    _add_common_attributes(self, site_url, {'email': self.email})
User.attributes_dict.__func__.__doc__ = \
    """Returns externally visible attributes of the user resource."""

User.get_absolute_url = models.permalink( \
    lambda self: \
        ('wwwhisper_user', (), {'uuid' : self.uuid}))

User.site = property(fget=lambda(self): self.get_profile().site, doc=\
"""Site to which the user belongs.""")

User.site_id = property(fget=lambda(self): self.get_profile().site_id, doc=\
"""Id of a site to which the user belongs.""")

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
      site: Site to which the location belongs.
      path: Canonical path of the location.
      uuid: Externally visible UUID of the location, allows to identify a REST
          resource representing the location.

      open_access: can be:
        disabled ('n') - only explicitly allowed users can access a location;
        enabled ('y') - everyone can access a location, no login is required;
        enabled with authentication ('a') - everyone can access a location
          but login is required.
    """
    OPEN_ACCESS_CHOICES = (
        ('n', 'no open access'),
        ('y', 'open access'),
        ('a', 'open access, login required'),
        )
    site = models.ForeignKey(Site, related_name='+')
    path = models.TextField(db_index=True)
    uuid = models.CharField(max_length=36, db_index=True,
                            editable=False, unique=True)
    open_access = models.CharField(max_length=2, choices=OPEN_ACCESS_CHOICES,
                                   default='n')

    def __init__(self, *args, **kwargs):
        super(Location, self).__init__(*args, **kwargs)
        self.update_cache()

    def update_cache(self):
        self._cached_permissions = [p for p in
                            Permission.objects.filter(http_location=self)]
        self.cache_mod_id = self.site.mod_id

    @check_cache
    def permissions(self):
        return self._cached_permissions

    def __unicode__(self):
        return "%s" % (self.path)

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = str(uuidgen.uuid4())
        return super(Location, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        """Constructs URL of the location resource."""
        return ('wwwhisper_location', (), {'uuid' : self.uuid})

    @modify_site
    def grant_open_access(self, require_login):
        """Allows open access to the location."""
        if require_login:
            self.open_access = 'a'
        else:
            self.open_access = 'y'
        self.save()

    def open_access_granted(self):
        return self.open_access in ('y', 'a')

    def open_access_requires_login(self):
        return self.open_access == 'a'

    @modify_site
    def revoke_open_access(self):
        """Disables open access to the location."""
        self.open_access = 'n'
        self.save()

    def can_access(self, user):
        """Determines if a user can access the location.

        Returns:
            True if the user is granted permission to access the
            location or it the location is open.
        """
        # Sanity check (this should normally be ensured by the caller).
        if user.site_id != self.site_id:
            return False
        return (self.open_access_granted()
                or filter(lambda perm: perm.user_id == user.id,
                          self.permissions()) != [])

    @modify_site
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
            LookupError: A site to which location belongs has no user
                with a given UUID.
        """
        user = _find(
            User, userextras__uuid=user_uuid, userextras__site_id=self.site_id)
        if user is None:
            raise LookupError('User not found')
        permission = _find(
            Permission, http_location_id=self.id, user_id=user.id)
        created = False
        if permission is None:
            created = True
            permission = Permission.objects.create(
                http_location_id=self.id, user_id=user.id)
        return (permission, created)

    @modify_site
    def revoke_access(self, user_uuid):
        """Revokes access to the location from a given user.

        Args:
            user_uuid: string UUID of a user.

        Raises:
            LookupError: Site has no user with a given UUID or the
                user can not access the location.
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
        user = _find(
            User, userextras__uuid=user_uuid, userextras__site_id=self.site_id)
        if user is None:
            raise LookupError('User not found.')
        permission = _find(
            Permission, http_location_id=self.id, user_id=user.id)
        if permission is None:
            raise LookupError('User can not access location.')
        return permission

    def allowed_users(self):
        """"Returns a list of users that can access the location."""
        return [permission.user for permission in self.permissions()]

    def attributes_dict(self, site_url):
        """Returns externally visible attributes of the location resource."""
        result = {
            'path': self.path,
            'allowedUsers': [
                user.attributes_dict(site_url) for user in self.allowed_users()
                ],
            }
        if self.open_access_granted():
            result['openAccess'] = {
                'requireLogin' : self.open_access_requires_login()
                }
        return _add_common_attributes(self, site_url, result)

class Permission(ValidatedModel):
    """Connects a location with a user that can access the location.

    Attributes:
        http_location: The location to which the Permission object gives access.
        user: The user that is given access to the location.
    """

    http_location = models.ForeignKey(Location, related_name='+')
    user = models.ForeignKey(User, related_name='+')

    def __unicode__(self):
        return "%s, %s" % (self.http_location, self.user.email)

    @models.permalink
    def get_absolute_url(self):
        """Constructs URL of the permission resource."""
        return ('wwwhisper_allowed_user', (),
                {'location_uuid' : self.http_location.uuid,
                 'user_uuid': self.user.uuid})

    def attributes_dict(self, site_url):
        """Returns externally visible attributes of the permission resource."""
        return _add_common_attributes(
            self, site_url, {'user': self.user.attributes_dict(site_url)})

class Collection(object):
    """A common base class for managing a collection of resources.

    All resources in a collection belong to a common site and only
    this site can manipulate the resouces.

    Resources in the collection are of the same type and need to be
    identified by an UUID.

    Attributes (Need to be defined in subclasses):
        item_name: Name of a resource stored in the collection.
        model_class: Class that manages storage of resources.
        site_id_column_name: Name of a column in the model class that stores
            a site_id of a resource.
        uuid_column_name: Name of a column in the model class that stores
            a resource uuid.
    """

    def __init__(self, site):
        self.site = site
        self.update_cache()

    def update_cache(self):
        filter_args = {self.site_id_column_name: self.site.site_id}
        self._cached_items = [item for item in
                      self.model_class.objects.filter(**filter_args)]
        self.cache_mod_id = self.site.mod_id

    @check_cache
    def all(self):
        return self._cached_items

    def get_unique(self, filter_fun):
        """Finds a unique item that satisfies a given filter.

        Returns:
           The item or None if not found.
        """
        result = filter(filter_fun, self.all())
        count = len(result)
        assert count <= 1
        if count == 0:
            return None
        return result[0]

    def find_item(self, uuid):
        return self.get_unique(lambda item: item.uuid == uuid)

    @modify_site
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
    uuid_column_name = 'userextras__uuid'
    site_id_column_name = 'userextras__site_id'

    def __init__(self, site):
        super(UsersCollection, self).__init__(site)

    @modify_site
    def create_item(self, email):
        """Creates a new User object for the site.

        There may be two different users with the same email but for
        different sites.

        Raises:
            ValidationError if the email is invalid or if a site
            already has a user with such email.
        """
        encoded_email = _encode_email(email)
        if encoded_email is None:
            raise ValidationError('Invalid email format.')
        if _find(User, email=encoded_email,
                 userextras__site_id=self.site.site_id) is not None:
            raise ValidationError('User already exists.')
        site = _find(Site, site_id=self.site.site_id)
        if site is None:
            raise ValidationError('site no longer exists.')
        while True:
            username = _gen_random_str(USERNAME_LEN)
            if _find(User, username=username) is None:
                break
        user = User.objects.create(
            username=username, email=encoded_email, is_active=True)
        extras = UserExtras.objects.create(
            user=user, site=site, uuid=str(uuidgen.uuid4()))
        return user

    def find_item_by_email(self, email):
        encoded_email = _encode_email(email)
        if encoded_email is None:
            return None
        return self.get_unique(lambda user: user.email == encoded_email)

class LocationsCollection(Collection):
    """Collection of locations resources."""

    item_name = 'location'
    model_class = Location
    uuid_column_name = 'uuid'
    site_id_column_name = 'site_id'

    def __init__(self, site):
        super(LocationsCollection, self).__init__(site)

    @modify_site
    def create_item(self, path):
        """Creates a new Location object for the site.

        The location path should be canonical and should not contain
        parts that are not used for access control (query, fragment,
        parameters). Location should not contain non-ascii characters.

        Raises:
            ValidationError if the path is invalid or if a site
            already has a location with such path.
        """

        if not url_path.is_canonical(path):
            raise ValidationError(
                'Path should be absolute and normalized (starting with / '\
                    'without /../ or /./ or //).')
        if url_path.contains_fragment(path):
            raise ValidationError(
                "Path should not contain fragment ('#' part).")
        if url_path.contains_query(path):
            raise ValidationError(
                "Path should not contain query ('?' part).")
        if url_path.contains_params(path):
            raise ValidationError(
                "Path should not contain parameters (';' part).")
        try:
            path.encode('ascii')
        except UnicodeError:
            raise ValidationError(
                'Path should contain only ascii characters.')

        if _find(Location, path=path, site=self.site) is not None:
            raise ValidationError('Location already exists.')

        location = Location.objects.create(path=path, site=self.site)
        return location


    @check_cache
    def find_location(self, canonical_path):
        """Finds a location that defines access to a given path on the site.

        Args:
            canonical_path: The path for which matching location is searched.

        Returns:
            The most specific location with path matching a given path or None
            if no matching location exists.
        """
        canonical_path_len = len(canonical_path)
        longest_matched_location = None
        longest_matched_location_len = -1

        for location in self.all():
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

    def has_open_location_with_login(self):
        for location in Location.objects.filter(site=self.site):
            if (location.open_access_granted() and
                location.open_access_requires_login()):
                return True
        return False

def _uuid2urn(uuid):
    return 'urn:uuid:' + uuid

def _add_common_attributes(item, site_url, attributes_dict):
    """Inserts common attributes of an item to a given dict.

    Attributes that are common for different resource types are a
    'self' link and an 'id' field.
    """
    attributes_dict['self'] = site_url + item.get_absolute_url()
    if hasattr(item, 'uuid'):
        attributes_dict['id'] = _uuid2urn(item.uuid)
    return attributes_dict

def _find(model_class, **kwargs):
    """Finds a single item satisfying a given expression.

    Args:
        model_class: Model that manages stored items.
        **kwargs: Filtering expression, at most one element can satisfy it.
    Returns:
        An item that satisfies expression or None.
    """
    items = [item for item in model_class.objects.filter(**kwargs)]
    count = len(items)
    assert count <= 1
    if count == 0:
        return None
    return items[0]

def _encode_email(email):
    """Encodes and validates email address.

    Email is converted to a lower case not to require emails to be added
    to the access control list with the same capitalization that the
    user signs-in with.
    """
    encoded_email = email.lower()
    if not _is_email_valid(encoded_email):
        return None
    return encoded_email

def _is_email_valid(email):
    """Validates email with a regexp defined by BrowserId:
    browserid/browserid/static/dialog/resources/validation.js
    """
    return re.match(
        "^[\w.!#$%&'*+\-/=?\^`{|}~]+@[a-z0-9-]+(\.[a-z0-9-]+)+$",
        email) != None

def _gen_random_str(length):
    secure_generator = random.SystemRandom()
    allowed_chars='abcdefghijklmnopqrstuvwxyz'\
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(
        [secure_generator.choice(allowed_chars) for i in range(length)])
