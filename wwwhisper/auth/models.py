from django.contrib.auth.models import User
from django.db import models

# Create your models here.

class HttpResource(models.Model):
    path = models.CharField(max_length=2000, null = False, primary_key=True)

    def __unicode__(self):
        return "%s" % (self.path)

class HttpPermission(models.Model):
    http_resource = models.ForeignKey(HttpResource)
    user = models.ForeignKey(User)
    #http_resource = models.CharField(max_length=2000, null = False)
    #user = models.CharField(max_length=100, null = False)
    #TODO: consts.
    #http_method = models.CharField(max_length=20, null = False)
    #allow = models.BooleanField(null = False)
    #subresources_inherit = models.BooleanField(null = False)


    def __unicode__(self):
        return "%s, %s" % (self.http_resource, self.user.email)
