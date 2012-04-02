from django.contrib.auth.models import User
from wwwhisper_auth.models import HttpResource
from wwwhisper_auth.models import HttpPermission

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

def grant_access(email, path):
    add_user(email)
    add_resource(path)
    user_id = User.objects.get(email=email).id
    return _add(HttpPermission, http_resource_id=path, user_id=user_id)

def revoke_access(email, path):
    return _del(HttpPermission, user__email=email, http_resource=path)

def allowed_emails(path):
    return [permission.user.email for permission in
            HttpPermission.objects.filter(http_resource=path)]

def can_access(email, path):
    path_len = len(path)
    longest_path_len = -1
    longest_path = ""
    for resource in HttpResource.objects.all():
        l = len(resource.path)
        if path.startswith(resource.path) and \
                l > longest_path_len and \
                (l == path_len or path[l] == '/'):
            longest_path_len = l
            longest_path = resource.path
    return longest_path_len != -1 and \
        _find(HttpPermission, user__email=email, http_resource=longest_path)

        # HttpPermission.objects.filter(user__email = email,
        #                               http_resource = longest_path).count() > 0
#    return _find(HttpPermission, user__email=email, http_resource=path)
