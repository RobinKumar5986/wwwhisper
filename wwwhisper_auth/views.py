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

"""Views that handle user authentication and authorization."""

from django.contrib import auth
from django.core.cache import cache
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import View
from wwwhisper_auth import http
from wwwhisper_auth import url_utils
from wwwhisper_auth.backend import AssertionVerificationException

import logging

logger = logging.getLogger(__name__)

def get_user(request):
    """Retrieves a user object associated with a given request.

    The user id of a logged in user is stored in the session key-value store.
    """
    user_id = request.session.get('user_id', None)
    if user_id is not None:
        return request.site.users.get_unique(lambda user: user.id == user_id)
    return None

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
        if url_utils.contains_fragment(encoded_path):
            path_validation_error = "Path should not include fragment ('#')"
        else:
            stripped_path = url_utils.strip_query(encoded_path)
            decoded_path = url_utils.decode(stripped_path)
            decoded_path = url_utils.collapse_slashes(decoded_path)
            if not url_utils.is_canonical(decoded_path):
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
                    self._html_or_none(request, 'not_authorized.html',
                                       {'email' : user.email}))
            response['User'] = user.email
            return response

        if (location is not None and location.open_access_granted() and
            not location.open_access_requires_login()):
            logger.debug('%s: authentication not required, access granted.'
                         % (debug_msg))
            return http.HttpResponseOK('Access granted.')
        logger.debug('%s: user not authenticated.' % (debug_msg))
        return http.HttpResponseNotAuthenticated(
            self._html_or_none(request, 'login.html', request.site.skin()))

    def _html_or_none(self, request, template, context={}):
        """Renders html response string from a given template.

        Returns None if request does not accept html response type.
        """
        if (http.accepts_html(request.META.get('HTTP_ACCEPT'))):
            return render_to_string(template, context)
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
            request.session['user_id'] = user.id
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
        # TODO: send a message to all processes to discard cached user session.
        response = http.HttpResponseNoContent()
        return response

class WhoAmI(http.RestView):
    """Allows to obtain an email of a currently logged in user."""

    def get(self, request):
        """Returns an email or an authentication required error."""
        user = get_user(request)
        if user is not None:
            return http.HttpResponseOKJson({'email': user.email})
        return http.HttpResponseNotAuthenticated()
