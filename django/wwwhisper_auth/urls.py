from django.conf.urls.defaults import patterns, url
from views import CsrfToken, Auth, Login, Logout
from models import UsersCollection

users_collection = UsersCollection()

urlpatterns = patterns(
    'wwwhisper_auth.views',
    url(r'^csrftoken/$', CsrfToken.as_view()),
    url(r'^login/$', Login.as_view(users_collection=users_collection)),
    url(r'^logout/$', Logout.as_view()),
    # TODO: is authorized?
    url(r'^is-authorized/$', Auth.as_view()),
    )
