from django.conf.urls.defaults import patterns, include, url
from django.contrib.auth.models import User
from views import Model, Permission
from views import Location, LocationCollection
from views import CollectionView, ItemView
from wwwhisper_auth.models import UserCollection

#TODO: clean urls!
urlpatterns = patterns(
    'wwwhisper_admin.views',
    url(r'^model.json/$', Model.as_view()),
    url(r'^users/$', CollectionView.as_view(collection=UserCollection)),
    url(r'^users/(?P<uuid>[0-9a-z-]+)/$', ItemView.as_view(model=User)),
    url(r'^locations/$', LocationCollection.as_view()),
    url(r'^locations/(?P<uuid>[0-9a-z-]+)/$', Location.as_view()),
    url(r'^permissions/$', Permission.as_view())
    )
