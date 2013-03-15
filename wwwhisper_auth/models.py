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

from django.contrib.auth.models import AbstractBaseUser
from django.db import connection
from django.db import models
from django.db import transaction
from django.forms import ValidationError
from functools import wraps
from wwwhisper_auth import  url_path
from wwwhisper_auth import  email_re

import logging
import random
import re
import uuid as uuidgen
import wwwhisper_auth.site_cache

logger = logging.getLogger(__name__)

class LimitExceeded(Exception):
    pass

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

      mod_id: Changed after any modification of site-related data (not
         only Site itself but also site's locations, permissions or
         users). Allows to determine when Django processes need to
         update cached data.
    """
    site_id = models.TextField(primary_key=True, db_index=True, editable=False)
    mod_id = models.IntegerField(default=0)

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.users_limit = None
        self.locations_limit = None

    def heavy_init(self):
        """Creates collections of all site-related data.

        This is a resource intensive operation that retrieves all site
        related data from the database. It is only performed if the site
        was modified since it was last retrieved.
        """
        self.locations = LocationsCollection(self)
        self.users = UsersCollection(self)

    def site_modified(self):
        """Increases site modification id.

        This causes the site to be refreshed in web processes caches.
        """
        cursor = connection.cursor()
        cursor.execute(
            'UPDATE wwwhisper_auth_site '
            'SET mod_id = mod_id + 1 WHERE site_id = %s', [self.site_id])
        self.mod_id = wwwhisper_auth.site_cache.get_mod_id(self, connection)
        transaction.commit_unless_managed()
        assert self.mod_id is not None

# TODO: Rename to avoid confusion with module name.
site_cache = wwwhisper_auth.site_cache.SiteCache()

def create_site(site_id):
    """Creates a new Site object.

    Args:
       site_id: A domain or other id of the created site.
    Raises:
       ValidationError if a site with such id already exists.
    """
    site =  Site.objects.create(site_id=site_id)
    site.heavy_init()
    site_cache.insert(site)
    return site

def find_site(site_id):
    site = site_cache.get(site_id)
    if site is not None:
        return site
    site = _find(Site, site_id=site_id)
    if site is not None:
        site.heavy_init()
        site_cache.insert(site)
    return site

def delete_site(site_id):
    site = find_site(site_id)
    if site is None:
        return False
    # Users, Locations and Permissions have foreign key to the Site
    # and are deleted automatically.
    map(lambda user: user.delete(), site.users.all())
    site_cache.delete(site_id)
    site.delete()
    # Makes sure error is raised if collections are accidentally
    # accessed after the site is deleted.
    site.locations.__dict__.clear()
    site.users.__dict__.clear()
    return True

def modify_site(decorated_method):
    """Must decorate all methods that change data associated with the site.

    Makes sure site is marked as modified and other Django processes
    will retrieve new data from the DB instead of using cached data.
    """

    @wraps(decorated_method)
    def wrapper(self, *args, **kwargs):
        result = decorated_method(self, *args, **kwargs)
        # If no exception.
        self.site.site_modified()
        return result
    return wrapper

class User(AbstractBaseUser):
    # Site to which the user belongs.
    site = models.ForeignKey(Site, related_name='+')

    # Externally visible UUID of the user. Allows to identify a REST
    # resource representing the user.
    uuid = models.CharField(max_length=36, db_index=True,
                            editable=False, unique=True)
    email = models.EmailField(db_index=True)

    USERNAME_FIELD = 'uuid'
    REQUIRED_FIELDS = ['email', 'site']

    def attributes_dict(self, site_url):
        """Returns externally visible attributes of the user resource."""
        return _add_common_attributes(self, site_url, {'email': self.email})

    @models.permalink
    def get_absolute_url(self):
        return ('wwwhisper_user', (), {'uuid' : self.uuid})

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

    def permissions(self):
        # Does not run a query to get permissions if not needed.
        return self.site.locations.get_permissions(self.id)

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
                or self.permissions().get(user.id) != None)

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
        user = self.site.users.find_item(uuid=user_uuid)
        if user is None:
            raise LookupError('User not found')
        permission = self.permissions().get(user.id)
        created = False
        if permission is None:
            created = True
            permission = Permission.objects.create(
                http_location_id=self.id, user_id=user.id, site_id=self.site_id)
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
        user = self.site.users.find_item(uuid=user_uuid)
        if user is None:
            raise LookupError('User not found.')
        permission = self.permissions().get(user.id)
        if permission is None:
            raise LookupError('User can not access location.')
        return permission

    def allowed_users(self):
        """"Returns a list of users that can access the location."""
        return [perm.user for perm in self.permissions().itervalues()]

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
    site = models.ForeignKey(Site, related_name='+')
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
        self._cached_items = []
        for item in self.model_class.objects.filter(**filter_args):
            self._cached_items.append(item)
            # Use already retrieved site, do not retrieve it again.
            item.site = self.site
        self.cache_mod_id = self.site.mod_id

    def is_cache_obsolete(self):
        return self.site.mod_id != self.cache_mod_id

    def all(self):
        if self.is_cache_obsolete():
            self.update_cache()
        return self._cached_items

    def count(self):
        return len(self.all())

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

    def do_create_item(self, *args, **kwargs):
        """Only to be called by subclasses."""
        item = self.model_class.objects.create(site=self.site, **kwargs)
        item.site = self.site
        return item

class UsersCollection(Collection):
    """Collection of users resources."""

    item_name = 'user'
    model_class = User
    uuid_column_name = 'uuid'
    site_id_column_name = 'site_id'

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
            LimitExceeded if the site defines a maximum number of
            users and adding a new one would exceed this number.
        """
        users_limit = self.site.users_limit
        if (users_limit is not None and self.count() >= users_limit):
            raise LimitExceeded('Users limit exceeded')

        encoded_email = _encode_email(email)
        if encoded_email is None:
            raise ValidationError('Invalid email format.')
        if self.find_item_by_email(encoded_email) is not None:
            raise ValidationError('User already exists.')
        return self.do_create_item(
            uuid=str(uuidgen.uuid4()), email=encoded_email)

    def find_item_by_email(self, email):
        encoded_email = _encode_email(email)
        if encoded_email is None:
            return None
        return self.get_unique(lambda user: user.email == encoded_email)

class LocationsCollection(Collection):
    """Collection of locations resources."""

    # Can be safely risen to whatever value is needed.
    PATH_LEN_LIMIT = 300

    # TODO: These should rather also be all caps.
    item_name = 'location'
    model_class = Location
    uuid_column_name = 'uuid'
    site_id_column_name = 'site_id'

    def __init__(self, site):
        super(LocationsCollection, self).__init__(site)

    def update_cache(self):
        super(LocationsCollection, self).update_cache()
        # Retrieves permissions for all locations of the site with a
        # single query.
        self._cached_permissions = {}
        for location in self.all():
            self._cached_permissions[location.id] = {}
        for p in Permission.objects.filter(site=self.site):
            self._cached_permissions[p.http_location_id][p.user_id] = p

    def get_permissions(self, location_id):
        """Returns permissions for a given location of the site."""
        if self.is_cache_obsolete():
            self.update_cache()
        return self._cached_permissions.get(location_id, {})

    @modify_site
    def create_item(self, path):
        """Creates a new Location object for the site.

        The location path should be canonical and should not contain
        parts that are not used for access control (query, fragment,
        parameters). Location should not contain non-ascii characters.

        Raises:
            ValidationError if the path is invalid or if a site
            already has a location with such path.
            LimitExceeded if the site defines a maximum number of
            locations and adding a new one would exceed this number.
        """

        locations_limit = self.site.locations_limit
        if (locations_limit is not None and self.count() >= locations_limit):
            raise LimitExceeded('Locations limit exceeded')

        if not url_path.is_canonical(path):
            raise ValidationError(
                'Path should be absolute and normalized (starting with / '\
                    'without /../ or /./ or //).')
        if len(path) > self.PATH_LEN_LIMIT:
            raise ValidationError('Path too long')
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

        if self.get_unique(lambda item: item.path == path) is not None:
            raise ValidationError('Location already exists.')

        return self.do_create_item(path=path)


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
        for location in self.all():
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
    return re.match(email_re.EMAIL_VALIDATION_RE, email)

def _gen_random_str(length):
    secure_generator = random.SystemRandom()
    allowed_chars='abcdefghijklmnopqrstuvwxyz'\
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(
        [secure_generator.choice(allowed_chars) for i in range(length)])
