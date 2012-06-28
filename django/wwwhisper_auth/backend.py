# wwwhisper - web access control.
# Copyright (C) 2012 Jan Wrobel <wrr@mixedbit.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
