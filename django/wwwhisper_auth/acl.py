from django.contrib.auth.models import User
from wwwhisper_auth.models import HttpResource
from wwwhisper_auth.models import HttpPermission

def _add(model_class, **kwargs):
    resource, created = model_class.objects.get_or_create(**kwargs)
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
    return [object.__dict__[field] for object in model_class.objects.all()]


def add_resource(path):
    return _add(HttpResource, path=path)

def del_resource(path):
    return _del(HttpResource, path=path)

def find_resource(path):
    return _find(HttpResource, path=path)

def paths():
    return _all(HttpResource, 'path')

def add_user(email):
    return _add(User, username=email, email=email, is_active=True)

def del_user(email):
    return _del(User, email=email)

def find_user(email):
    return _find(User, email=email)

def emails():
    return _all(User, 'email')


