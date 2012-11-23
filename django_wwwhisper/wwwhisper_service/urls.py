from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^auth/api/', include('wwwhisper_auth.urls')),
    url(r'^admin/api/', include('wwwhisper_admin.urls')),
)
