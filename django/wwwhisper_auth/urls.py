from django.conf.urls.defaults import patterns, include, url
from views import CsrfToken, Auth, Login, Logout

urlpatterns = patterns(
    'wwwhisper_auth.views',
    url(r'^csrftoken/$', CsrfToken.as_view()),
    url(r'^login/$', Login.as_view()),
    url(r'^logout/$', Logout.as_view()),
    url(r'^noauthorized/$', 'noauthorized'),
    #url(r'^browserid/', include('django_browserid.urls')),
    # TODO: is authorized?
    url(r'^$', Auth.as_view()),
    )
