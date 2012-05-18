from django.conf.urls.defaults import patterns, include, url
from django.contrib.auth.models import User
from views import Model, Permission
from views import CollectionView, ItemView
from wwwhisper_auth.acl import UserCollection, LocationCollection

#TODO: clean urls!
user_collection = UserCollection()
location_collection = LocationCollection()

urlpatterns = patterns(
    'wwwhisper_admin.views',
    url(r'^model.json/$',
        Model.as_view()),
    url(r'^users/$',
        CollectionView.as_view(collection=user_collection)),
    url(r'^users/(?P<uuid>[0-9a-z-]+)/$',
        ItemView.as_view(collection=user_collection)),
    url(r'^locations/$',
        CollectionView.as_view(collection=location_collection)),
    url(r'^locations/(?P<uuid>[0-9a-z-]+)/$',
        ItemView.as_view(collection=location_collection)),
    url(r'^permissions/$',
        Permission.as_view())
    )
