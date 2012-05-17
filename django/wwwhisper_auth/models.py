from django.conf import settings
from django.contrib.auth.models import User as AuthUser
from django.db import models
from django.db.models.signals import post_save

import re
import uuid

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

def _find(model_class, **kwargs):
    count = model_class.objects.filter(**kwargs).count()
    assert count <= 1
    return count > 0

def _all(model_class, field):
    return [obj.__dict__[field] for obj in model_class.objects.all()]

def site_url():
    return getattr(settings, 'SITE_URL',
                   'WARNING: SITE_URL is not set')

def full_url(absolute_path):
    return site_url() + absolute_path

def urn_from_uuid(uuid):
    return 'urn:uuid:' + uuid

# TODO: just location?
class HttpLocation(models.Model):
    path = models.CharField(max_length=2000, null=False, primary_key=True)

    def __unicode__(self):
        return "%s" % (self.path)

class HttpPermission(models.Model):
    http_location = models.ForeignKey(HttpLocation)
    # TODO: rename to allowed_user
    user = models.ForeignKey(AuthUser)

    def __unicode__(self):
        return "%s, %s" % (self.http_location, self.user.email)

class CreationException(Exception):
    pass;

def add_user(email):
    if find_user(email):
        return False
    AuthUser.objects.create(username=uuid.uuid4(), email=email, is_active=True)
    return True;

def del_user(email):
    return _del(AuthUser, email=email)

def find_user(email):
    return _find(AuthUser, email=email)

# TODO: capital letters in email are not accepted
def is_email_valid(email):
    """Validates email with regexp defined by BrowserId:
    browserid/browserid/static/dialog/resources/validation.js
    """
    return re.match(
        "^[\w.!#$%&'*+\-/=?\^`{|}~]+@[a-z0-9-]+(\.[a-z0-9-]+)+$",
        email) != None


def attributes_dict(self):
    return {
        'self': full_url(self.get_absolute_url()),
        'email': self.email,
        'id': urn_from_uuid(self.username),
        }
AuthUser.attributes_dict = attributes_dict

class User:
    collection_name = 'users'
    item_name = 'user'

    @staticmethod
    def create_item(email):
        if not is_email_valid(email):
            raise CreationException('Invalid email format.')
        if find_user(email):
            raise CreationException('User already exists.')
        return AuthUser.objects.create(
            username=str(uuid.uuid4()), email=email, is_active=True)

    @staticmethod
    def all():
        return AuthUser.objects.all()


#    def create_item(email)

# TODO: remove this:
class UserProfile(models.Model):
    user = models.OneToOneField(AuthUser)
#    uuid = models.CharField(max_length=36, null=False, primary_key=True,
#                            editable=False)

    def save(self, *args, **kwargs):
#        if not self.uuid:
#            self.uuid = uuid.uuid4()
        return super(UserProfile, self).save(*args, **kwargs)


def create_user_extras(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_extras, sender=AuthUser)
