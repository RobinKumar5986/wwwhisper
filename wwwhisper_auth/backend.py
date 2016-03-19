# wwwhisper - web access control.
# Copyright (C) 2012-2016 Jan Wrobel <jan@mixedbit.org>

"""Authentication backend used by wwwhisper_auth."""

from django.contrib.auth.backends import ModelBackend
from django.forms import ValidationError
from django_browserid import RemoteVerifier, BrowserIDException
from models import LimitExceeded

class AuthenticationError(Exception):
    pass

class BrowserIDBackend(ModelBackend):
    """"Backend that verifies BrowserID assertion.

    Similar backend is defined in django_browserid application. It is not
    used here, because it does not allow to distinguish between an
    assertion verification error and an unknown user.
    """

    def __init__(self):
        self.verifier = RemoteVerifier()

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
            AuthenticationError: verification failed.
        """
        try:
            result = self.verifier.verify(assertion=assertion,
                                          audience=site_url)
        except BrowserIDException as ex:
            return AuthenticationError(
                'Failed to contact Persona verification service')
        if not result:
            raise AuthenticationError(
                'BrowserID assertion verification failed.')
        user = site.users.find_item_by_email(result.email)
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
                return site.users.create_item(result.email)
            else:
                return None
        except ValidationError as ex:
            raise AuthenticationError(', '.join(ex.messages))
        except LimitExceeded as ex:
            raise AuthenticationError(str(ex))


class VerifiedEmailBackend(ModelBackend):
    """"Backend that authenticates the user using verified email"""

    def authenticate(self, site, site_url, verified_email):
        """verified_email was encoded in a signed token. A caller
        responsibility is to check token validity and decode the token
        data (the reason why the backend does not decode tokens, is
        that token data includes also redirection path, that can't be
        easily passed backed from this method).

        Returns:
             Object that represents a user with the verified email
             passed to this method If a user with such email does not
             exists, but there are open locations that require login,
             the user object is created. In other cases, None is
             returned.

        Raises:
            AuthenticationError: verification failed.
        """
        user = site.users.find_item_by_email(verified_email)
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
                return site.users.create_item(verified_email)
            else:
                return None
        except ValidationError as ex:
            raise AuthenticationError(', '.join(ex.messages))
        except LimitExceeded as ex:
            raise AuthenticationError(str(ex))
