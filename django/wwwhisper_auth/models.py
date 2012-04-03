from django.contrib.auth.models import User
from django.db import models

class HttpLocation(models.Model):
    path = models.CharField(max_length=2000, null = False, primary_key=True)

    def __unicode__(self):
        return "%s" % (self.path)


class HttpPermission(models.Model):
    http_location = models.ForeignKey(HttpLocation)
    # TODO: rename to allowed_user
    user = models.ForeignKey(User)

    def __unicode__(self):
        return "%s, %s" % (self.http_location, self.user.email)

