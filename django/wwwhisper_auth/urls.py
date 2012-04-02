from django.conf.urls.defaults import patterns, include, url
from views import CsrfToken, Logout

urlpatterns = patterns(
    'wwwhisper_auth.views',
    url(r'^csrftoken/$', CsrfToken.as_view()),
    url(r'^login/$', 'login'),
    url(r'^logout/$', Logout.as_view()),
    url(r'^noauthorized/$', 'noauthorized'),
    url(r'^verify/$', 'verify'),
    #url(r'^browserid/', include('django_browserid.urls')),
    url(r'^$', 'auth'),
    )
