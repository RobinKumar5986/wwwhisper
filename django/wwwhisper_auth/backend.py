"""Authentication backend used by wwwhisper_auth."""

from django.contrib.auth.backends import ModelBackend
from django_browserid.base import verify
from wwwhisper_auth import models

class AssertionVerificationException(Exception):
    """Raised when BrowserId assertion was not verified successfully."""
    pass

class BrowserIDBackend(ModelBackend):
    """"Backend that verifies BrowserID assertion.

    Similar backend is defined in django_browserid application. It is not
    used here, because it does not allow to distinguish between an
    assertion verification error and an unknown user.

    Attributes:
        users_collection: Allows to find a user with a given email.
    """
    users_collection = models.UsersCollection()

    def authenticate(self, assertion):
        """Verifies BrowserID assertion

        Returns:
             Object that represents a user with an email verified by
             the assertion. None if user with such email does not exist.

        Raises:
            AssertionVerificationException: verification failed.
        """
        result = verify(assertion=assertion, audience=models.SITE_URL)
        if not result:
            raise AssertionVerificationException(
                'BrowserID assertion verification failed.')
        return self.users_collection.find_item_by_email(result['email'])
