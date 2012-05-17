from django.conf.urls.defaults import patterns, include, url
from views import User, UserCollection, Model, Permission, Location

#TODO: clean urls!
urlpatterns = patterns(
    'wwwhisper_admin.views',
    url(r'^model.json/$', Model.as_view()),
    url(r'^users/$', UserCollection.as_view()),
    url(r'^users/(?P<uuid>[0-9a-z-]+)/$', User.as_view()),
    url(r'^locations/$', Location.as_view()),
    url(r'^permissions/$', Permission.as_view())
    )
