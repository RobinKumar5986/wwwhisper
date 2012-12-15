from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

SITE_URL = getattr(settings, 'SITE_URL', None)
if SITE_URL is None:
    raise ImproperlyConfigured(
        'WWWhisper requires SITE_URL to be set in django settings.py file')

class SiteMiddleware(object):
    """Sets site id and site url for a request.

    At the moment a single site configured in settings.py is supported.
    """
    def process_request(self, request):
        request.site_id = SITE_URL
        request.site_url = SITE_URL
        return None
