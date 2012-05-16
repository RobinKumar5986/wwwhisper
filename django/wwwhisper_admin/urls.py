from django.conf.urls.defaults import patterns, include, url
from views import User, User2, Model, Permission, Location

#TODO: clean urls!
urlpatterns = patterns(
    'wwwhisper_admin.views',
    url(r'^model.json/$', Model.as_view()),
    #TODO: use plulars?
    url(r'^user/$', User.as_view()),
    url(r'^user/(?P<uuid>[\d-]+)/$', User2.as_view()),
    url(r'^location/$', Location.as_view()),
    url(r'^permission/$', Permission.as_view())
    )
