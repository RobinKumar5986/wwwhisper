# wwwhisper - web access control.
# Copyright (C) 2012, 2013 Jan Wrobel <wrr@mixedbit.org>
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

"""Views that handle user authentication and authorization."""

from django.conf import settings
from django.contrib import auth
from django.core.context_processors import csrf
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.vary import vary_on_headers
from django.views.generic import View
from functools import wraps
from wwwhisper_auth import http
from wwwhisper_auth import url_path
from wwwhisper_auth.backend import AssertionVerificationException

import logging
import os

logger = logging.getLogger(__name__)

class UserData:
    def __init__(self, user):
        self.id = user.id
        self.uuid = user.uuid
        self.email = user.email
        self.site_id = user.site_id
        self.mod_id = user.site.mod_id

def get_user(request):
    """Retrieves up-to-date user object associated with a given request.

    The user object is retrieved from the session key-value store if
    the site was not modified since the object was put there. If the
    site was modified, the user is retrieved from the DB and the
    session is updated.
    """

    cached_user = request.session.get('user-data', None)
    if cached_user is not None:
        if cached_user.site_id != request.site.site_id:
            return None
        if cached_user.mod_id == request.site.mod_id:
            return cached_user
    # Makes sure user is authenticated and belongs to the current
    # site (auth backend just ensures user exists).
    user = request.user
    if not user.is_authenticated() or user.site_id != request.site.site_id:
        return None
    cached_user = UserData(user)
    request.session['user-data'] = cached_user
    return cached_user

class Auth(View):
    """Handles auth request from the HTTP server.

    Auth request determines whether a user is authorized to access a
    given location. It must be sent by the HTTP server for each
    request to wwwhisper protected location. Auth request includes all
    headers of the original request and a path the original request is
    trying to access. The result of the request determines the action
    to be performed by the HTTP server:

      401: The user is not authenticated (no valid session cookie
           set).

      403: The user is authenticated (the request contains a valid
           session cookie) but is not authorized to access the
           location. The error should be passed to the user. The
           'User' header in the returned response containts email of
           the user.

      400: Request is malformed (suspicious path format, 'User' header
           set in the request, ...).

      200: User is authenticated and authorized to access the location
           or the location does not require authorization. The
           original request should be allowed. The 'User' header in
           the returned response containts email of the user.

      Any other result code should be passed to the user without
      granting access.

      Auth view does not need to be externally accessible.
    """

    assets = None

    @http.never_ever_cache
    def get(self, request):
        """Invoked by the HTTP server with a single path argument.

        The HTTP server should pass the path argument verbatim,
        without any transformations or decoding. Access control
        mechanism should work on user visible paths, not paths after
        internal rewrites performed by the server.

        At the moment, the path is allowed to contain a query part,
        which is ignored (this is because nginx does not expose
        encoded path without the query part).

        The method follows be conservative in what you accept
        principle. The path should be absolute and normalized, without
        fragment id, otherwise access is denied. Browsers in normal
        operations perform path normalization and do not send fragment
        id. Multiple consecutive '/' separators are permitted, because
        these are not normalized by browsers, and are used by
        legitimate applications.  Paths with '/./' and '/../', should
        not be normally sent by browsers and can be a sign of
        something suspicious happening. It is extremely important that
        wwwhisper does not perform any path transformations that are
        not be compatible with transformations done by the HTTP
        server.
       """
        encoded_path = self._extract_encoded_path_argument(request)
        if encoded_path is None:
            return http.HttpResponseBadRequest(
                "Auth request should have 'path' argument.")

        # Do not allow requests that contain the 'User' header. The
        # header is passed to backends and must be guaranteed to be
        # set by wwwhisper.
        # This check should already be performed by HTTP server.
        if 'HTTP_USER' in request.META:
            return http.HttpResponseBadRequest(
                "Client can not set the 'User' header")

        debug_msg = "Auth request to '%s'" % (encoded_path)

        path_validation_error = None
        if url_path.contains_fragment(encoded_path):
            path_validation_error = "Path should not include fragment ('#')"
        else:
            stripped_path = url_path.strip_query(encoded_path)
            decoded_path = url_path.decode(stripped_path)
            decoded_path = url_path.collapse_slashes(decoded_path)
            if not url_path.is_canonical(decoded_path):
                path_validation_error = 'Path should be absolute and ' \
                    'normalized (starting with / without /../ or /./ or //).'
        if path_validation_error is not None:
            logger.debug('%s: incorrect path.' % (debug_msg))
            return http.HttpResponseBadRequest(path_validation_error)

        user = get_user(request)
        location = request.site.locations.find_location(decoded_path)
        if user is not None:

            debug_msg += " by '%s'" % (user.email)
            respone = None

            if location is not None and location.can_access(user):
                logger.debug('%s: access granted.' % (debug_msg))
                response =  http.HttpResponseOK('Access granted.')
            else:
                logger.debug('%s: access denied.' % (debug_msg))
                response = http.HttpResponseNotAuthorized(
                    self._html_body(request, http.HttpResponseNotAuthorized))
            response['User'] = user.email
            return response

        if (location is not None and location.open_access_granted() and
            not location.open_access_requires_login()):
            logger.debug('%s: authentication not required, access granted.'
                         % (debug_msg))
            return http.HttpResponseOK('Access granted.')
        logger.debug('%s: user not authenticated.' % (debug_msg))
        return http.HttpResponseNotAuthenticated(
            self._html_body(request, http.HttpResponseNotAuthenticated))

    def _html_body(self, request, response_class):
        """Returns html response body suitable for a given class of response.

        Returns None if request does not accept html or static files are not
        configured.
        """
        if (self.assets and
            http.accepts_html(request.META.get('HTTP_ACCEPT'))):
            return self.assets[response_class].body
        return None

    @staticmethod
    def _extract_encoded_path_argument(request):
        """Get 'path' argument or None.

        Standard Django mechanism for accessing arguments is not used
        because path is needed in a raw, encoded form. Django would
        decode it, making it impossible to correctly recognize the
        query part and to determine if the path contains fragment.
        """
        request_path_and_args = request.get_full_path()
        assert request_path_and_args.startswith(request.path)
        args = request_path_and_args[len(request.path):]
        if not args.startswith('?path='):
            return None
        return args[len('?path='):]

class CsrfToken(View):
    """Establishes Cross Site Request Forgery protection token."""

    @http.never_ever_cache
    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        """Sets a cookie with CSRF protection token.

        The method must be called if the cookie is missing before any
        CSRF protected HTTP method is called (all HTTP methods of
        views that extend RestView). Returned token must be set in
        'X-CSRFToken' header when the protected method is called,
        otherwise the call fails. It is enough to get the token once
        and reuse it for all subsequent calls to CSRF protected
        methods.
        """
        return http.HttpResponseNoContent()

class Login(http.RestView):
    """Allows a user to authenticates with BrowserID."""

    def post(self, request, assertion):
        """Logs a user in (establishes a session cookie).

        Verifies BrowserID assertion and check that a user with an
        email verified by the BrowserID is known (added to users
        list).
        """
        if assertion == None:
            return http.HttpResponseBadRequest('BrowserId assertion not set.')
        try:
            user = auth.authenticate(site=request.site,
                                     site_url=request.site_url,
                                     assertion=assertion)
        except AssertionVerificationException as ex:
            logger.debug('Assertion verification failed.')
            return http.HttpResponseBadRequest(str(ex))
        if user is not None:
            auth.login(request, user)

            # Store all user data needed by Auth view in session, this
            # way, user table does not need to be queried during the
            # performance critical request (sessions are cached).
            request.session['user-data'] = UserData(user)
            logger.debug('%s successfully logged.' % (user.email))
            return http.HttpResponseNoContent()
        else:
            # Unkown user.
            # Return not authorized because request was well formed (400
            # doesn't seem appropriate).
            return http.HttpResponseNotAuthorized()

class Logout(http.RestView):
    """Allows a user to logout."""

    def post(self, request):
        """Logs a user out (invalidates a session cookie)."""
        auth.logout(request)
        # Modify site, so other Django processes reject cached user session.
        request.site.site_modified()
        response = http.HttpResponseNoContent()
        response.delete_cookie(settings.SESSION_COOKIE_NAME)
        response.delete_cookie(settings.CSRF_COOKIE_NAME)
        return response

class WhoAmI(View):
    """Allows to obtain an email of a currently logged in user."""

    @http.disallow_cross_site_request
    @method_decorator(cache_page(60 * 60 * 5))
    @method_decorator(cache_control(private=True))
    @vary_on_headers('Cookie')
    def get(self, request):
        """Returns an email or an authentication required error."""
        user = get_user(request)
        if user is not None:
            return http.HttpResponseOKJson({'email': user.email})
        return http.HttpResponseNotAuthenticated()
