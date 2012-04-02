from django.conf.urls.defaults import patterns, include, url
from views import Contact, Model, Permission, Resource

#TODO: clean urls!
urlpatterns = patterns(
    'wwwhisper_admin.views',
    url(r'^model.json$', Model.as_view()),
    url(r'^contact$', Contact.as_view()),
    url(r'^resource$', Resource.as_view()),
    url(r'^permission$', Permission.as_view())
    )
