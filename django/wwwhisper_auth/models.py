from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
import uuid

# TODO: just location?
class HttpLocation(models.Model):
    path = models.CharField(max_length=2000, null=False, primary_key=True)

    def __unicode__(self):
        return "%s" % (self.path)

class HttpPermission(models.Model):
    http_location = models.ForeignKey(HttpLocation)
    # TODO: rename to allowed_user
    user = models.ForeignKey(User)

    def __unicode__(self):
        return "%s, %s" % (self.http_location, self.user.email)

# TODO: remove this:
class UserProfile(models.Model):
    user = models.OneToOneField(User)
#    uuid = models.CharField(max_length=36, null=False, primary_key=True,
#                            editable=False)

    def save(self, *args, **kwargs):
#        if not self.uuid:
#            self.uuid = uuid.uuid4()
        return super(UserProfile, self).save(*args, **kwargs)


def create_user_extras(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_extras, sender=User)
