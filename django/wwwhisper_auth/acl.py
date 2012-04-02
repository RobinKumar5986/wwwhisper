from django.contrib.auth.models import User
from wwwhisper_auth.models import HttpResource
from wwwhisper_auth.models import HttpPermission

def _add(model_class, **kwargs):
    resource, created = model_class.objects.get_or_create(**kwargs)
    return created

def add_resource(path):
    return _add(HttpResource, path=path)
#    resource, created = HttpResource.objects.get_or_create(path=path)
#    return created

def del_resource(path):
    resource = HttpResource.objects.filter(path=path)
    assert resource.count() <= 1
    if resource.count() == 0:
        return False
    resource.delete()
    return True

def find_resource(path):
    count = HttpResource.objects.filter(path=path).count()
    assert count <= 1
    return count > 0

def paths():
    return [resource.path for resource in HttpResource.objects.all()]


def add_user(email):
    user, created = User.objects.get_or_create(
        username=email, email=email, is_active=True)
    return created

def del_user(email):
    user = User.objects.filter(email=email)
    assert user.count() <= 1
    if user.count() == 0:
        return False
    user.delete()
    return True

def find_user(email):
    count = User.objects.filter(email=email).count()
    assert count <= 1
    return count > 0

def emails():
    return [user.email for user in User.objects.all()]


