from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save

import re
import uuid

# TODO: remove duplication.
def _add(model_class, **kwargs):
    obj, created = model_class.objects.get_or_create(**kwargs)
    return created

# TODO: remove duplication.
def _find(model_class, **kwargs):
    item = model_class.objects.filter(**kwargs)
    count = item.count()
    assert count <= 1
    return item.get()

# TODO: just location?
class HttpLocation(models.Model):
    path = models.CharField(max_length=2000, null=False, primary_key=True)
    uuid = models.CharField(max_length=36, null=False, db_index=True,
                            editable=False)
    def __unicode__(self):
        return "%s" % (self.path)

    def attributes_dict(self):
        return {'path': self.path}

    def grant_access(self, user_uuid):
        user = _find(User, username=user_uuid)
        if user is None:
            raise LookupError('User does not exist')
        return _add(HttpPermission, http_location_id=self.path, user_id=user.id)

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
        return super(HttpLocation, self).save(*args, **kwargs)

class HttpPermission(models.Model):
    http_location = models.ForeignKey(HttpLocation)
    # TODO: rename to allowed_user
    user = models.ForeignKey(User)

    def __unicode__(self):
        return "%s, %s" % (self.http_location, self.user.email)

#    def create_item(email)

# TODO: remove this:
class UserProfile(models.Model):
    user = models.OneToOneField(User)
#    uuid = models.CharField(max_length=36, null=False, primary_key=True,
#                            editable=False)

    def save(self, *args, **kwargs):
#        if not self.uuid:
#            self.uuid = uuid.uuid4()
        return super(UserProfile, self).save(*args, **kwargs)


User.attributes_dict = lambda(self): {'email': self.email}
User.uuid = property(lambda(self): self.username)

def create_user_extras(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_extras, sender=User)
