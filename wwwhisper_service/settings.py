# Django settings for wwwhisper_service project.

DEBUG = False
TEMPLATE_DEBUG = DEBUG


# If WWWHISPER_STATIC is set, wwwhisper serves static html resources
# needed for login and for the admin application (this is not needed
# if these resources are served directly by a frontend server).
#
# In addition, auth request returns html documents to be displayed to
# the user along with 401 and 403 responses. This is also not always
# needed. For example, nginx_auth_request module can not pass returned
# response body to the user, so needs to obtain this documents from a
# separate location or with a separate request.
WWWHISPER_STATIC = None

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
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

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

MIDDLEWARE_CLASSES = (
    #'wwwhisper_service.profile.ProfileMiddleware',
    'django.middleware.common.CommonMiddleware',
    # Must be placed before session middleware to alter session cookies.
    'wwwhisper_auth.protect_cookies.ProtectCookiesMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    'wwwhisper_auth.site.SiteMiddleware',
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
    'django_browserid',
    'wwwhisper_auth',
    'wwwhisper_admin'
)

if DEBUG:
    INSTALLED_APPS += ('debug_toolbar',)

AUTH_PROFILE_MODULE = 'wwwhisper_auth.UserExtras'

AUTHENTICATION_BACKENDS = (
    'wwwhisper_auth.backend.BrowserIDBackend',
)

BROWSERID_VERIFICATION_URL = 'https://verifier.login.persona.org/verify'

ABSOLUTE_URL_OVERRIDES = {
    'auth.user': lambda u: "/admin/api/users/%s/" % u.username,
}

if not TESTING:
    LEVEL = {True: 'DEBUG', False: 'INFO'}[DEBUG]
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(asctime)s %(name)s %(message)s'
                },
            'simple': {
                'format': '%(levelname)s %(name)s %(message)s'
                },
            },
        'handlers': {
            'console':{
                'level':LEVEL,
                'class':'logging.StreamHandler',
                'formatter': 'simple'
                },
            },
        'loggers': {
            'django_browserid': {
                'handlers':['console'],
                'propagate': True,
                'level':LEVEL,
                },
            'wwwhisper_auth': {
                'handlers':['console'],
                'propagate': True,
                'level':LEVEL,
                },
            'wwwhisper_admin': {
                'handlers':['console'],
                'propagate': True,
                'level':LEVEL,
                },
            'wwwhisper_heroku': {
                'handlers':['console'],
                'propagate': True,
                'level':LEVEL,
                },
            'django.request': {
                'handlers': ['console'],
                'propagate': True,
                'level': LEVEL,
                },
            }
        }

if not SECRET_KEY:
    raise ImproperlyConfigured('DJANGO_SECRET_KEY environment variable not set')
