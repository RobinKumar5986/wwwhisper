from django.conf.urls.defaults import patterns, include, url
from views import User, User2, Model, Permission, Location

#TODO: clean urls!
urlpatterns = patterns(
    'wwwhisper_admin.views',
    url(r'^model.json/$', Model.as_view()),
    url(r'^users/$', User.as_view()),
    url(r'^users/(?P<uuid>[\d-]+)/$', User2.as_view()),
    url(r'^locations/$', Location.as_view()),
    url(r'^permissions/$', Permission.as_view())
    )
