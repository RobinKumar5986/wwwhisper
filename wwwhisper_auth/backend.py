# wwwhisper - web access control.
# Copyright (C) 2012 Jan Wrobel <wrr@mixedbit.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
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

        locations_collection: Allows to check if a site has open
            locations that require login. If this is the case and
            unknown user signs-in, user object for her needs to be
            created.
    """
    users_collection = models.UsersCollection()
    locations_collection = models.LocationsCollection()

    def authenticate(self, assertion):
        """Verifies BrowserID assertion

        Returns:
             Object that represents a user with an email verified by
             the assertion. If a user with such email does not exists,
             but there are open locations that require login, the user
             object is created. In other cases, None is returned.

        Raises:
            AssertionVerificationException: verification failed.
        """
        url = models.site_url()
        result = verify(assertion=assertion, audience=url)
        if not result:
            raise AssertionVerificationException(
                'BrowserID assertion verification failed.')
        email = result['email']
        user = self.users_collection.find_item_by_email(url, result['email'])
        if user is not None:
            return user
        try:
            # The site has open locations that require login, every
            # user needs to be allowed.
            #
            # TODO: user objects created in such way should probably
            # be marked and automatically deleted on logout or after
            # some time of inactivity.
            if self.locations_collection.has_open_location_with_login(url):
                return self.users_collection.create_item(url, email)
            else:
                return None
        except models.CreationException as ex:
            raise AssertionVerificationException(str(ex))
