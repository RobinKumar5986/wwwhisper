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

# TODO: How to handle trailing '/'? Maybe remove it prior to adding path to db?
def can_access(email, path):
    path_len = len(path)
    longest_match = ""
    longest_match_len = -1

    for probed_path in paths():
        probed_path_len = len(probed_path)
        stripped_probed_path = probed_path.rstrip('/')
        stripped_probed_path_len = len(stripped_probed_path)
        if (path.startswith(stripped_probed_path) and
            probed_path_len > longest_match_len and
            (stripped_probed_path_len == path_len
             or path[stripped_probed_path_len] == '/')):
            longest_match_len = probed_path_len
            longest_match = probed_path
    return longest_match_len != -1 and \
        _find(HttpPermission, user__email=email, http_resource=longest_match)
