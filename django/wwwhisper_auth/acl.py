from wwwhisper_auth.models import HttpResource
from wwwhisper_auth.models import HttpPermission

def add_resource(path):
    resource, created = HttpResource.objects.get_or_create(path = path)
    return created

def del_resource(path):
    resource = HttpResource.objects.filter(path = path)
    assert resource.count() <= 1
    if resource.count() == 0:
        return False
    resource.delete()
    return True

def resource_exists(path):
    count = HttpResource.objects.filter(path = path).count()
    assert count <= 1
    return count > 0
