# wwwhisper - web access control.
# Copyright (C) 2012-2015 Jan Wrobel <jan@mixedbit.org>

"""wwwhisper authentication and authorization.

The package defines model that associates users with locations that
each user can access and exposes API for checking and manipulating
permissions. It also provides REST API to login, logout a
user and to check if a currently logged in user can access a given
location.
"""

from django.conf import settings
from django.db.models import signals
from django.contrib.auth.management import create_superuser
from django.contrib.auth import models as auth_app
from django.core.exceptions import ImproperlyConfigured
from wwwhisper_auth import models

# Disable default behaviour for admin user creation (interactive
# question).
signals.post_syncdb.disconnect(
    create_superuser,
    sender=auth_app,
    dispatch_uid = "django.contrib.auth.management.create_superuser")
