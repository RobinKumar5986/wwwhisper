from django.test import TestCase
import wwwhisper_auth.acl as acl

class Acl(TestCase):
    def test_add_resource(self):
        self.assertFalse(acl.find_resource('/foo/bar'))
        self.assertTrue(acl.add_resource('/foo/bar'))
        self.assertTrue(acl.find_resource('/foo/bar'))

    def test_add_resource_twice(self):
        self.assertTrue(acl.add_resource('/foo/bar'))
        self.assertFalse(acl.add_resource('/foo/bar'))

    def test_del_resource(self):
        self.assertTrue(acl.add_resource('/foo/bar'))
        self.assertTrue(acl.del_resource('/foo/bar'))
        self.assertFalse(acl.find_resource('/foo/bar'))

    def test_del_missing_resource(self):
        self.assertFalse(acl.del_resource('/foo/bar'))

    def test_get_resources(self):
        acl.add_resource('/foo/bar')
        acl.add_resource('/baz/bar')
        self.assertEqual(sorted(acl.resources()), ['/baz/bar', '/foo/bar'])
        acl.del_resource('/foo/bar')
        self.assertEqual(acl.resources(), ['/baz/bar'])

    def test_get_resources_when_empty(self):
        self.assertEqual(acl.resources(), [])
