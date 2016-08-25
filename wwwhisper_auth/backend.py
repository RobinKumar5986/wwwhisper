# wwwhisper - web access control.
# Copyright (C) 2012-2016 Jan Wrobel <jan@mixedbit.org>

"""Authentication backend used by wwwhisper_auth."""

from django.contrib.auth.backends import ModelBackend
from django.forms import ValidationError

from wwwhisper_auth import login_token
from wwwhisper_auth.models import LimitExceeded

class AuthenticationError(Exception):
    pass

class VerifiedEmailBackend(ModelBackend):
    """"Backend that authenticates the user using verified email"""

    def authenticate(self, site, site_url, token):
        """Token was a part of a login url that proves email ownership.

        Returns:
             Object that represents a user with the verified email
             encoded in the token. If a user with such email does not
             exists, but there are open locations that require login,
             the user object is created. In other cases, None is
             returned.
        Raises:
            AuthenticationError: token is invalid, expired or
            generated for a different site. Token is valid, but the
            user does not exist yet and can't be added because user
            limit is exceeded (this can happen only if site has open
            locations that require login).
        """
        verified_email = login_token.load_login_token(site, site_url, token)
        if verified_email is None:
            raise AuthenticationError('Token invalid or expired.')

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
            # Should not happen, because email in the signed token is
            # validated before the token is generated.
            raise AuthenticationError(', '.join(ex.messages))
        except LimitExceeded as ex:
            raise AuthenticationError(str(ex))
