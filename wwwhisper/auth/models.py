from django.contrib.auth.models import User
from django.db import models

class HttpResource(models.Model):
    path = models.CharField(max_length=2000, null = False, primary_key=True)

    def __unicode__(self):
        return "%s" % (self.path)

class HttpPermission(models.Model):
    http_resource = models.ForeignKey(HttpResource)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return "%s, %s" % (self.http_resource, self.user.email)
