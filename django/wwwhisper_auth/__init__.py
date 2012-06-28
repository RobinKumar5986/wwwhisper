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
from django.db.models import signals
from django.contrib.auth.management import create_superuser
from django.contrib.auth import models as auth_app
from django.core.exceptions import ImproperlyConfigured
from wwwhisper_auth import models

def create_admin_users(app, created_models, *args, **kwargs):
    """Adds admin users to Users table when the table is created.

    Emails of admin users should be listed in settings.py. Admin users
    can access all locations.
    """
    if auth_app.User in created_models:
        admins_emails = getattr(settings, 'WWWHISPER_ADMINS', None)
        if admins_emails is None:
            return
        for email in admins_emails:
            users_collection = models.UsersCollection()
            try:
                user = users_collection.create_item(email)
            except models.CreationException as ex:
                raise ImproperlyConfigured('Failed to create admin user %s: %s'
                                           % (email, ex));

# Disable default behaviour for admin user creation (interactive
# question).
signals.post_syncdb.disconnect(
    create_superuser,
    sender=auth_app,
    dispatch_uid = "django.contrib.auth.management.create_superuser")

# Instead, invoke create_admin_users function defined in this module.
signals.post_syncdb.connect(
    create_admin_users,
    sender=auth_app,
    dispatch_uid = "django.contrib.auth.management.create_superuser")
