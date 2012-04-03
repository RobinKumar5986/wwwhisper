from django.contrib.auth.models import User
from wwwhisper_auth.models import HttpLocation
from wwwhisper_auth.models import HttpPermission

import re

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

def add_location(path):
    return _add(HttpLocation, path=path)

def del_location(path):
    return _del(HttpLocation, path=path)

def find_location(path):
    return _find(HttpLocation, path=path)

def locations():
    return _all(HttpLocation, 'path')

def is_email_valid(email):
    """Validates email with regexp defined by BrowserId:
    browserid/browserid/static/dialog/resources/validation.js
    """
    return re.match("^[\w.!#$%&'*+\-/=?\^`{|}~]+@[a-z0-9-]+(\.[a-z0-9-]+)+$",
                    email) != None

def add_user(email):
    return _add(User, username=email, email=email, is_active=True)

def del_user(email):
    return _del(User, email=email)

def find_user(email):
    return _find(User, email=email)

def emails():
    return _all(User, 'email')

def grant_access(email, location_path):
    if not find_location(location_path):
        raise LookupError('Location does not exist')
    add_user(email)
    user_id = User.objects.get(email=email).id
    return _add(HttpPermission, http_location_id=location_path, user_id=user_id)

def revoke_access(email, location_path):
    if not find_location(location_path):
        raise LookupError('Location does not exist')
    return _del(HttpPermission, user__email=email, http_location=location_path)

# TODO: should this work only for defined locations or check parent locations?
def allowed_emails(path):
    return [permission.user.email for permission in
            HttpPermission.objects.filter(http_location=path)]

# TODO: How to handle trailing '/'? Maybe remove it prior to adding path to db?
def can_access(email, path):
    path_len = len(path)
    longest_match = ""
    longest_match_len = -1

    for probed_path in locations():
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
        _find(HttpPermission, user__email=email, http_location=longest_match)
