# wwwhisper - web access control.
# Copyright (C) 2016 Jan Wrobel <jan@mixedbit.org>

from django.conf import settings
from django.core import signing

def generate_login_token(site_url, email, path):
    """Returns a signed token to login a user with a given email.

    The token should be emailed to the user to verify that the user
    indeed owns the email.

    The token is valid only for the given site (it will be discarded
    if it is submitted to a different site protected by the same
    wwwhisper instance).

    path specifies where the user should be redirected after login.
    """
    token_data = {
        'site': site_url,
        'email': email,
        'path': path
    }
    return signing.dumps(token_data, salt=site_url, compress=True)

def load_login_token(site_url, token):
    """Verifies the login token.

    Returns (email, path) if the token is valid, None otherwise.
    """
    try:
        token_data = signing.loads(
            token, salt=site_url, max_age=settings.AUTH_TOKEN_SECONDS_VALID)
        # site_url in the token seems like an overkill. site_url is
        # already used as salt which should give adequate protection
        # against using a token for sites different than the one for
        # which the token was generated.
        if token_data['site'] != site_url:
            return None
        return (token_data['email'], token_data['path'])
    except signing.BadSignature:
        return None
