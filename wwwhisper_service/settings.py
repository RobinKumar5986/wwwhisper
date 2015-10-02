# Django settings for wwwhisper_service project.

DEBUG = False
TEMPLATE_DEBUG = DEBUG


# If WWWHISPER_STATIC is set, wwwhisper serves static html resources
# needed for login and for the admin application (this is not needed
# if these resources are served directly by a frontend server).
WWWHISPER_STATIC = None
# Serve all wwwhisper resources from /wwwhisper/ prefix (/wwwhisper/auth/,
# /wwwhisper/admin/)
WWWHISPER_PATH_PREFIX = 'wwwhisper/'
# Static files are also served from /wwwhisper/ prefix.
import cdn_container
STATIC_URL = cdn_container.CDN_CONTAINER + '/' + 'wwwhisper/'

import os
import sys

TESTING = sys.argv[1:2] == ['test']

if TESTING:
    from test_site_settings import *
else:
    from site_settings import *


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# Postgres backend requires this to be set.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = False

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#        'LOCATION': 'unique-snowflake'
    }
}

if DEBUG:
    INTERNAL_IPS = ('127.0.0.1',)

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
# Site-Url from frontend server is validated by wwwhisper (checked
# against a list of aliases that are stored in the DB) and set in the
# X-Forwarded-Host. Host header is not used.
ALLOWED_HOSTS = ['*']

MIDDLEWARE_CLASSES = (
    #'wwwhisper_service.profile.ProfileMiddleware',
    # Must go before CommonMiddleware, to set a correct url to which
    # CommonMiddleware redirects.
    'wwwhisper_auth.middleware.SetSiteMiddleware',
    'wwwhisper_auth.middleware.SiteUrlMiddleware',
    'django.middleware.common.CommonMiddleware',
    # Must be placed before session middleware to alter session cookies.
    'wwwhisper_auth.middleware.ProtectCookiesMiddleware',
    'wwwhisper_auth.middleware.SecuringHeadersMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

# Don't use just sessionid, to avoid collision with apps protected by wwwhisper.
SESSION_COOKIE_NAME = 'wwwhisper-sessionid'
CSRF_COOKIE_NAME = 'wwwhisper-csrftoken'

# Make session cookie valid only until a browser closes.
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True

ROOT_URLCONF = 'wwwhisper_service.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'wwwhisper_service.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django_browserid',
    'wwwhisper_auth',
    'wwwhisper_admin'
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
TEMPLATE_DIRS = (
    os.path.join(PROJECT_DIR, 'templates'),
)

AUTH_USER_MODEL = 'wwwhisper_auth.User'

AUTHENTICATION_BACKENDS = (
    'wwwhisper_auth.backend.BrowserIDBackend',
)

BROWSERID_VERIFICATION_URL = 'https://verifier.login.persona.org/verify'

ABSOLUTE_URL_OVERRIDES = {
    'auth.user': lambda u: "/admin/api/users/%s/" % u.username,
}

handler = 'logging.StreamHandler' if not TESTING \
    else 'django.utils.log.NullHandler'
level = 'INFO' if not DEBUG else 'DEBUG'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(name)s %(message)s'
            },
        # See http://docs.python.org/2/library/logging.html#logrecord-attributes
        'simple': {
            'format': '%(levelname)s %(name)s %(message)s'
            },
        },
    'handlers': {
        'console':{
            'level': level,
            'class': handler,
            'formatter': 'simple'
            },
        },
    'loggers': {
        'django_browserid': {
            'handlers': ['console'],
            'propagate': True,
            'level': level,
            },
        'wwwhisper_service': {
            'handlers': ['console'],
            'propagate': True,
            'level': level,
            },
        'wwwhisper_auth': {
            'handlers': ['console'],
            'propagate': True,
            'level': level,
            },
        'wwwhisper_admin': {
            'handlers': ['console'],
            'propagate': True,
            'level': level,
            },
        'django.request': {
            'handlers': ['console'],
            'propagate': True,
            'level': level,
            },
        'django.db': {
            'handlers': ['console'],
            'propagate': True,
            'level': level,
            },
        }
    }

if not SECRET_KEY:
    raise ImproperlyConfigured('DJANGO_SECRET_KEY environment variable not set')
