from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save

import re
import uuid

# TODO: can this warning be fatal initialization error?
def site_url():
    return getattr(settings, 'SITE_URL',
                   'WARNING: SITE_URL is not set')

def full_url(absolute_path):
    return site_url() + absolute_path

def urn_from_uuid(uuid):
    return 'urn:uuid:' + uuid

# TODO: make it a member?
def add_common_attributes(item, attributes_dict):
    attributes_dict['self'] = full_url(item.get_absolute_url())
    if hasattr(item, 'uuid'):
        attributes_dict['id'] = urn_from_uuid(item.uuid)
    return attributes_dict

# TODO: remove duplication.
def _add(model_class, **kwargs):
    obj, created = model_class.objects.get_or_create(**kwargs)
    return created

def _del(model_class, **kwargs):
    object_to_del = model_class.objects.filter(**kwargs)
    assert object_to_del.count() <= 1
    if object_to_del.count() == 0:
        return False
    object_to_del.delete()
    return True

# TODO: remove duplication.
def _find(model_class, **kwargs):
    item = model_class.objects.filter(**kwargs)
    count = item.count()
    assert count <= 1
    if count == 0:
        return None
    return item.get()

# TODO: just location?
class HttpLocation(models.Model):
    path = models.CharField(max_length=2000, null=False, primary_key=True)
    uuid = models.CharField(max_length=36, null=False, db_index=True,
                            editable=False)
    def __unicode__(self):
        return "%s" % (self.path)

    def attributes_dict(self):
        return add_common_attributes(self, {
                'path': self.path,
                'allowedUsers': self.allowed_users(),
                })

    def grant_access(self, user_uuid):
        user = _find(User, username=user_uuid)
        if user is None:
            raise LookupError('User not found')
        # TODO: test what happens when created twice.
        return HttpPermission.objects.create(
            http_location_id=self.path, user_id=user.id)

    def revoke_access(self, user_uuid):
        user = _find(User, username=user_uuid)
        if user is None:
            raise LookupError('User not found')
        if not _del(HttpPermission, http_location_id=self.path,
                    user_id=user.id):
            raise LookupError('User can not access location.')

    def allowed_users(self):
        return [permission.user.attributes_dict() for permission in
                HttpPermission.objects.filter(http_location=self.path)]

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
        return super(HttpLocation, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('wwwhisper_location', (), {'uuid' : self.uuid})

# TODO: rename to allowed_user
class HttpPermission(models.Model):
    http_location = models.ForeignKey(HttpLocation)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return "%s, %s" % (self.http_location, self.user.email)

    def attributes_dict(self):
        return add_common_attributes(
            self, {'user': self.user.attributes_dict()})

    @models.permalink
    def get_absolute_url(self):
        return ('wwwhisper_allowed_user', (),
                {'location_uuid' : self.http_location.uuid,
                 'user_uuid': self.user.uuid})

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


User.uuid = property(lambda(self): self.username)

# TODO: get_attributes_dict for symmetry with get_absolute_url?
User.attributes_dict = lambda(self): \
    add_common_attributes(self, {'email': self.email})

def create_user_extras(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_extras, sender=User)
