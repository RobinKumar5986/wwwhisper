# wwwhisper - web access control.
# Copyright (C) 2012 Jan Wrobel <wrr@mixedbit.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import signals
from django.contrib.auth.management import create_superuser
from django.contrib.auth import models as contrib_auth_models
from django.core.exceptions import ImproperlyConfigured
from wwwhisper_auth import models as auth_models

def enable_access_to_admin(app, created_models, *args, **kwargs):
    """Configures which users can initially access the admin applications.

    The function is invoked when the wwwhisper database is
    created. Users with emails listed in the WWWHISPER_ADMINS list are
    granted access to the admin application. Other than that, there is
    no difference between admin users and other users. The admin
    application manages access to itself, so it can be used to add and
    remove users that can perform administrative operations.
    """
    if (contrib_auth_models.User in created_models and
        kwargs.get('interactive', True)):

        admins_emails = getattr(settings, 'WWWHISPER_ADMINS', None)
        if admins_emails is None:
            return
        users_collection = auth_models.UsersCollection()
        locations_collection = auth_models.LocationsCollection()
        admin_location = locations_collection.create_item('/admin')

        for email in admins_emails:
            try:
                user = users_collection.create_item(email)
                admin_location.grant_access(user.uuid)
            except auth_models.CreationException as ex:
                raise ImproperlyConfigured('Failed to create admin user %s: %s'
                                           % (email, ex));

# Disable default behaviour for admin user creation (interactive
# question).
signals.post_syncdb.disconnect(
    create_superuser,
    sender=contrib_auth_models,
    dispatch_uid = "django.contrib.auth.management.create_superuser")

# Instead, invoke enable_access_to_admin function defined in this module.
signals.post_syncdb.connect(
    enable_access_to_admin,
    sender=contrib_auth_models,
    dispatch_uid = "django.contrib.auth.management.create_superuser")
