from django.conf.urls.defaults import patterns, url
from views import CsrfToken, Auth, Login, Logout

urlpatterns = patterns(
    'wwwhisper_auth.views',
    url(r'^csrftoken/$', CsrfToken.as_view()),
    url(r'^login/$', Login.as_view()),
    url(r'^logout/$', Logout.as_view()),
    # TODO: is authorized?
    url(r'^is_authorized/$', Auth.as_view()),
    )
