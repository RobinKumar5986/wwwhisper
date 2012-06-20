"""Urls exposed by the wwwhisper_auth application.

is-authorized/ URL does not need to be exposed by the HTTP server to
the outside world, other views need to be externally accessible.
"""

from django.conf.urls.defaults import patterns, url
from views import Auth, CsrfToken, Login, Logout
from wwwhisper_auth.models import LocationsCollection

urlpatterns = patterns(
    'wwwhisper_auth.views',
    url(r'^csrftoken/$', CsrfToken.as_view()),
    url(r'^login/$', Login.as_view()),
    url(r'^logout/$', Logout.as_view()),
    url(r'^is-authorized/$', Auth.as_view(
            locations_collection=LocationsCollection())),
    )
