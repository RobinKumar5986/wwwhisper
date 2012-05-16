from django.conf.urls.defaults import patterns, include, url
from views import User, Model, Permission, Location

#TODO: clean urls!
urlpatterns = patterns(
    'wwwhisper_admin.views',
    url(r'^model.json/$', Model.as_view()),
    #TODO: use plulars?
    url(r'^user/$', User.as_view()),
    url(r'^location/$', Location.as_view()),
    url(r'^permission/$', Permission.as_view())
    )
