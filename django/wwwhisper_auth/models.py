from django.contrib.auth.models import User
from django.db import models

class HttpResource(models.Model):
    path = models.CharField(max_length=2000, null = False, primary_key=True)

    def __unicode__(self):
        return "%s" % (self.path)

def add_resource(path):
    HttpResource(path = path).save()

class HttpPermission(models.Model):
    http_resource = models.ForeignKey(HttpResource)
    # TODO: rename to allowed_user
    user = models.ForeignKey(User)

    def __unicode__(self):
        return "%s, %s" % (self.http_resource, self.user.email)

