# wwwhisper - web access control.
# Copyright (C) 2012, 2013, 2014 Jan Wrobel <wrr@mixedbit.org>
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
from django.forms import ValidationError
from django_browserid.base import verify
from models import LimitExceeded

class AssertionVerificationException(Exception):
    """Raised when BrowserId assertion was not verified successfully."""
    pass

class BrowserIDBackend(ModelBackend):
    """"Backend that verifies BrowserID assertion.

    Similar backend is defined in django_browserid application. It is not
    used here, because it does not allow to distinguish between an
    assertion verification error and an unknown user.
    """

    # TODO: Put site_url in the model and find it based on id. Allow
    # for aliases.
    def authenticate(self, site, site_url, assertion):
        """Verifies BrowserID assertion

        Returns:
             Object that represents a user with an email verified by
             the assertion. If a user with such email does not exists,
             but there are open locations that require login, the user
             object is created. In other cases, None is returned.

        Raises:
            AssertionVerificationException: verification failed.
        """
        result = verify(assertion=assertion, audience=site_url)
        if not result:
            # TODO: different error if Persona is down.
            raise AssertionVerificationException(
                'BrowserID assertion verification failed.')
        email = result['email']
        user = site.users.find_item_by_email(result['email'])
        if user is not None:
            return user
        try:
            # The site has open locations that require login, every
            # user needs to be allowed.
            #
            # TODO: user objects created in such way should probably
            # be marked and automatically deleted on logout or after
            # some time of inactivity.
            if site.locations.has_open_location_with_login():
                return site.users.create_item(email)
            else:
                return None
        except ValidationError as ex:
            raise AssertionVerificationException(', '.join(ex.messages))
        except LimitExceeded as ex:
            raise AssertionVerificationException(str(ex))
