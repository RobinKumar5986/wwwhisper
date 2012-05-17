from django.test import TestCase
from wwwhisper_auth.models import User

class Model(TestCase):
    def test_is_email_valid(self):
        """Test strings taken from BrowserId tests."""
        self.assertTrue(User.is_email_valid('x@y.z'))
        self.assertTrue(User.is_email_valid('x@y.z.w'))
        self.assertTrue(User.is_email_valid('x.v@y.z.w'))
        self.assertTrue(User.is_email_valid('x_v@y.z.w'))

        self.assertFalse(User.is_email_valid('x'))
        self.assertFalse(User.is_email_valid('x@y'))
        self.assertFalse(User.is_email_valid('@y.z'))
        self.assertFalse(User.is_email_valid('z@y.z@y.z'))
        self.assertFalse(User.is_email_valid(''))

