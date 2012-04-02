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

    def test_get_paths(self):
        acl.add_resource('/foo/bar')
        acl.add_resource('/baz/bar')
        self.assertEqual(['/baz/bar', '/foo/bar'], sorted(acl.paths()))
        acl.del_resource('/foo/bar')
        self.assertEqual(['/baz/bar'], acl.paths())

    def test_get_paths_when_empty(self):
        self.assertEqual([], acl.paths())

    def test_add_user(self):
        self.assertFalse(acl.find_user('foo@example.com'))
        self.assertTrue(acl.add_user('foo@example.com'))
        self.assertTrue(acl.find_user('foo@example.com'))

    def test_add_user_twice(self):
        self.assertTrue(acl.add_user('foo@example.com'))
        self.assertFalse(acl.add_user('foo@example.com'))

    def test_del_user(self):
        self.assertTrue(acl.add_user('foo@example.com'))
        self.assertTrue(acl.del_user('foo@example.com'))
        self.assertFalse(acl.find_user('foo@example.com'))

    def test_del_missing_user(self):
        self.assertFalse(acl.del_user('foo@example.com'))

    def test_get_emails(self):
        acl.add_user('foo@example.com')
        acl.add_user('bar@example.com')
        self.assertEqual(['bar@example.com', 'foo@example.com'],
                         sorted(acl.emails()))
        acl.del_user('foo@example.com')
        self.assertEqual(['bar@example.com'], acl.emails())

    def test_get_emails_when_empty(self):
        self.assertEqual([], acl.emails())

    def test_grant_access(self):
        acl.add_user('foo@example.com')
        acl.add_resource('/foo/bar')
        self.assertFalse(acl.can_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.grant_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar'))

    def test_grant_access_for_non_existing_user(self):
        acl.add_resource('/foo/bar')
        self.assertFalse(acl.find_user('foo@example.com'))
        self.assertTrue(acl.grant_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.find_user('foo@example.com'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar'))

    def test_grant_access_to_non_existing_path(self):
        acl.add_user('foo@example.com')
        self.assertFalse(acl.find_resource('/foo/bar'))
        self.assertTrue(acl.grant_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.find_resource('/foo/bar'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar'))

    def test_grant_access_if_already_granted(self):
        self.assertTrue(acl.grant_access('foo@example.com', '/foo/bar'))
        self.assertFalse(acl.grant_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar'))

    def test_grant_access_gives_access_to_subpaths(self):
        self.assertTrue(acl.grant_access('foo@example.com', '/foo/bar'))

        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar/'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar/b'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar/baz'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar/baz/bar/'))

        self.assertFalse(acl.can_access('foo@example.com', '/foo/ba'))
        self.assertFalse(acl.can_access('foo@example.com', '/foo/barr'))
        self.assertFalse(acl.can_access('foo@example.com', '/foo/foo/bar'))

    def test_more_specific_path_takes_precedence_over_shorter_path(self):
        self.assertTrue(acl.grant_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.add_resource('/foo/bar/baz/'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar/ba'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar/bazz'))

        self.assertFalse(acl.can_access('foo@example.com', '/foo/bar/baz'))
        self.assertFalse(acl.can_access('foo@example.com', '/foo/bar/baz/'))
        self.assertFalse(acl.can_access('foo@example.com', '/foo/bar/baz/bam'))

    def test_trailing_slash_ignored(self):
        self.assertTrue(acl.grant_access('foo@example.com', '/foo/bar/'))

        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar/'))

        self.assertFalse(acl.can_access('foo@example.com', '/foo/barr'))
        self.assertFalse(acl.can_access('foo@example.com', '/foo/ba/'))

    def test_grant_access_to_root(self):
        self.assertTrue(acl.grant_access('foo@example.com', '/'))

        self.assertTrue(acl.can_access('foo@example.com', '/'))
        self.assertTrue(acl.can_access('foo@example.com', '/f'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar/baz'))

    def test_revoke_access(self):
        self.assertTrue(acl.grant_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.can_access('foo@example.com', '/foo/bar'))
        self.assertTrue(acl.revoke_access('foo@example.com', '/foo/bar'))
        self.assertFalse(acl.can_access('foo@example.com', '/foo/bar'))

    def test_revoke_non_granted_access(self):
        self.assertFalse(acl.revoke_access('foo@example.com', '/foo/bar'))

    def test_get_allowed_emails(self):
        acl.grant_access('foo@example.com', '/foo/bar')
        acl.grant_access('baz@example.com', '/foo/baz')
        acl.grant_access('bar@example.com', '/foo/bar')

        self.assertEqual(['bar@example.com', 'foo@example.com'],
                         sorted(acl.allowed_emails('/foo/bar')))
        self.assertEqual(['baz@example.com'], acl.allowed_emails('/foo/baz'))

        acl.revoke_access('foo@example.com', '/foo/bar')
        self.assertEqual(['bar@example.com'], acl.allowed_emails('/foo/bar'))

    def test_get_allowed_emails_when_empty(self):
        self.assertEqual([], acl.allowed_emails('/foo/bar'))

    # TODO: test that removing user and resource revokes access
