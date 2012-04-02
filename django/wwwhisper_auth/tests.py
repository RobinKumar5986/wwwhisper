from django.test import TestCase
import wwwhisper_auth.acl as acl

class Acl(TestCase):
    def test_add_resource(self):
        self.assertFalse(acl.resource_exists('/test/path'))
        self.assertTrue(acl.add_resource('/test/path'))
        self.assertTrue(acl.resource_exists('/test/path'))

    def test_add_resource_twice(self):
        self.assertTrue(acl.add_resource('/test/path'))
        self.assertFalse(acl.add_resource('/test/path'))

    def test_del_resource(self):
        self.assertTrue(acl.add_resource('/test/path'))
        self.assertTrue(acl.resource_exists('/test/path'))
        self.assertTrue(acl.del_resource('/test/path'))
        self.assertFalse(acl.resource_exists('/test/path'))

    def test_del_missing_resource(self):
        self.assertFalse(acl.del_resource('/test/path'))
