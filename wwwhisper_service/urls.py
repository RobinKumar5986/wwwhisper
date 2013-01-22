from django.conf.urls.defaults import *
from django.conf import settings
from wwwhisper_auth.assets import Asset, HtmlFileView

import logging

logger = logging.getLogger(__name__)


urlpatterns = patterns(
    '',
    url(r'^auth/api/', include('wwwhisper_auth.urls')),
    url(r'^admin/api/', include('wwwhisper_admin.urls')),
    )

if settings.WWWHISPER_STATIC is not None:
    logger.debug('wwwhisper configured to serve static files.')
    admin = Asset(settings.WWWHISPER_STATIC, 'admin', 'index.html')
    overlay = Asset(settings.WWWHISPER_STATIC, 'auth', 'overlay.html')
    login = Asset(settings.WWWHISPER_STATIC, 'auth', 'login.html')
    logout = Asset(settings.WWWHISPER_STATIC, 'auth', 'logout.html')
    goodbye = Asset(settings.WWWHISPER_STATIC, 'auth', 'goodbye.html')

    urlpatterns += patterns(
        '',
        url(r'^admin/$', HtmlFileView.as_view(asset=admin)),
        url(r'^auth/overlay.html$', HtmlFileView.as_view(asset=overlay)),
        url(r'^auth/login/$', HtmlFileView.as_view(asset=login)),
        url(r'^auth/login.html$', HtmlFileView.as_view(asset=login)),
        url(r'^auth/logout/$', HtmlFileView.as_view(asset=logout)),
        url(r'^auth/logout.html$', HtmlFileView.as_view(asset=logout)),
        url(r'^auth/goodbye.html$', HtmlFileView.as_view(asset=goodbye)),
        )

