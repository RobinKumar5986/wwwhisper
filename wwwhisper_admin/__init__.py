# wwwhisper - web access control.
# Copyright (C) 2012 Jan Wrobel <wrr@mixedbit.org>
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

"""wwwhisper admin API.

The package exposes REST API for specifying which users can access
which locations.
"""

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import signals
from django.contrib.auth.management import create_superuser
from django.contrib.auth import models as contrib_auth_models
from django.core.exceptions import ImproperlyConfigured
from wwwhisper_auth import models as auth_models

SITE_URL = getattr(settings, 'SITE_URL', None)
if SITE_URL is None:
    raise ImproperlyConfigured(
        'WWWhisper requires SITE_URL to be set in django settings.py file')

def _create_site():
    """Creates a site configured in settings.py.

    This is intermediate approach, wwwhisper is prepared to handle
    multiple sites, but currently it handles only a single one.
    """
    try:
        auth_models.create_site(SITE_URL)
    except auth_models.CreationException as ex:
        raise ImproperlyConfigured('Failed to create site %s: %s'
                                   % (SITE_URL, ex))

def _create_initial_locations():
    """Creates all locations listed in WWWHISPER_INITIAL_LOCATIONS setting."""
    locations_collection = auth_models.LocationsCollection()
    locations_paths = getattr(settings, 'WWWHISPER_INITIAL_LOCATIONS', [])
    for path in locations_paths:
        try:
            locations_collection.create_item(SITE_URL, path)
        except auth_models.CreationException as ex:
            raise ImproperlyConfigured('Failed to create location %s: %s'
                                       % (path, ex))

def _create_initial_admins():
    """Creates all users listed in WWWHISPER_INITIAL_ADMINS setting."""
    users_collection = auth_models.UsersCollection()
    emails = getattr(settings, 'WWWHISPER_INITIAL_ADMINS', [])
    for email in emails:
        try:
            user = users_collection.create_item(SITE_URL, email)
        except auth_models.CreationException as ex:
            raise ImproperlyConfigured('Failed to create admin user %s: %s'
                                       % (email, ex))

def _grant_admins_access_to_all_locations():
    for user in auth_models.UsersCollection().all(SITE_URL):
        for location in auth_models.LocationsCollection().all(SITE_URL):
            location.grant_access(user.uuid)

def grant_initial_permission(app, created_models, *args, **kwargs):
    """Configures initial permissions for wwwhisper protected site.

    Allows users with emails listed on WWWHISPER_INITIAL_ADMINS to
    access locations listed on WWWHISPER_INITIAL_LOCATIONS. The
    function is invoked when the wwwhisper database is created.
    Initial access rights is the only difference between users listed
    on WWWHISPER_INITIAL_ADMINS and other users. The admin application
    manages access to itself, so it can be used to add and remove
    users that can perform administrative operations.
    """
    if (contrib_auth_models.User in created_models and
        kwargs.get('interactive', True)):
        _create_site()
        _create_initial_locations()
        _create_initial_admins()
        _grant_admins_access_to_all_locations()

# Disable default behaviour for admin user creation (interactive
# question).
signals.post_syncdb.disconnect(
    create_superuser,
    sender=contrib_auth_models,
    dispatch_uid = "django.contrib.auth.management.create_superuser")

# Instead, invoke grant_initial_permission function defined in this module.
signals.post_syncdb.connect(
    grant_initial_permission,
    sender=contrib_auth_models,
    dispatch_uid = "django.contrib.auth.management.create_superuser")
