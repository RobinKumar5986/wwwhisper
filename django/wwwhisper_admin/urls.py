from django.conf.urls.defaults import patterns, include, url
from views import User, UserCollection, Model, Permission
from views import Location, LocationCollection
from views import UserCollectionStrategy, CollectionView
from wwwhisper_auth.models import User as UserModel

#TODO: clean urls!
urlpatterns = patterns(
    'wwwhisper_admin.views',
    url(r'^model.json/$', Model.as_view()),
#    url(r'^users/$', UserCollection.as_view()),
    url(r'^users/$', CollectionView.as_view(model=UserModel)),
    url(r'^users/(?P<uuid>[0-9a-z-]+)/$', User.as_view()),
    url(r'^locations/$', LocationCollection.as_view()),
    url(r'^locations/(?P<uuid>[0-9a-z-]+)/$', Location.as_view()),
    url(r'^permissions/$', Permission.as_view())
    )
