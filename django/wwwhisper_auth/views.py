"""Views that handle user authentication and authorization."""

from django.core.context_processors import csrf
from django.http import HttpResponse
from django.template import Context, loader
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import View
from wwwhisper_auth.backend import AssertionVerificationException
from wwwhisper_auth.http import HttpResponseBadRequest
from wwwhisper_auth.http import HttpResponseJson
from wwwhisper_auth.http import RestView

import django.contrib.auth as contrib_auth
import logging
import wwwhisper_auth.url_path as url_path

logger = logging.getLogger(__name__)

class Auth(View):
    """Handles auth request from the HTTP server.

    Auth request determines whether a user is authorized to access a
    given location. It must be sent by the HTTP server for each
    request to wwwhisper protected location. Auth request includes all
    headers of the original request and a path the original request is
    trying to access. The result of the request determines the action
    to be performed by the HTTP server:

      401: The user is not authenticated (no valid session cookie set).
           and should be presented with a login page.

      403: The user is authenticated (the request contains a valid
           session cookie) but is not authorized to access the
           location. The error should be passed to the user.

      200: User is authenticated and authorized to access the
           location or the location does not require authorization.
           The original request should be allowed.

      Any other result code should be passed to the user without
      granting access.

      Auth view does not need to be externally accessible.
    """

    locations_collection = None

    @method_decorator(never_cache)
    def get(self, request):
        """Invoked by the HTTP server with a single path argument.

        The HTTP server should pass the path argument verbatim,
        without any transformations or decoding. Access control
        mechanism should work on user visible paths, not paths after
        internal rewrites performed by the server.

        At the moment, the path is allowed to contain a query part,
        which is ignored (this is because nginx does not expose
        encoded path without the query part).

        The method follows 'be conservative in what you accept
        principle'. The path should be absolute and normalized,
        without fragment id, otherwise access is denied. Browsers in
        normal operations perform path normalization and do not send
        fragment id. Not normalized paths can be a sign of something
        suspicious happening. It is extremely important that
        wwwhisper does not perform any tricky path transformations
        that may not be compatible with transformations done by the
        HTTP server.
       """
        encoded_path = self._extract_encoded_path_argument(request)
        if encoded_path is None:
            return HttpResponseBadRequest(
                "Auth request should have 'path' argument.")
        debug_msg = "Auth request to '%s'" % (encoded_path)

        path_validation_error = None
        if url_path.contains_fragment(encoded_path):
            path_validation_error = "Path should not include fragment ('#')"
        else:
            stripped_path = url_path.strip_query(encoded_path)
            decoded_path = url_path.decode(stripped_path)
            if not url_path.is_canonical(decoded_path):
                path_validation_error = 'Path should be absolute and ' \
                    'normalized (starting with / without /../ or /./ or //).'
        if path_validation_error is not None:
            logger.debug('%s: incorrect path.' % (debug_msg))
            return HttpResponseBadRequest(path_validation_error)

        user = request.user
        location = self.locations_collection.find_parent(decoded_path)

        if user and user.is_authenticated():
            debug_msg += " by '%s'" % (user.email)

            if location is not None and location.can_access(user.uuid):
                logger.debug('%s: access granted.' % (debug_msg))
                return HttpResponse('Access granted.')
            logger.debug('%s: access denied.' % (debug_msg))
            template = loader.get_template('auth/not_authorized.html')
            context = Context({'email' : user.email})
            return HttpResponse(template.render(context), status=403)

        if location is not None and location.open_access:
            logger.debug('%s: authentication not required, access granted.'
                         % (debug_msg))
            return HttpResponse('Access granted.')
        logger.debug('%s: user not authenticated.' % (debug_msg))
        return HttpResponse('Login required.', status=401)

    @staticmethod
    def _extract_encoded_path_argument(request):
        """Extracts an encoded value of request 'path' argument.

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

    @never_cache
    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        """Returns CSRF protection token in a cookie and a response body.

        The GET must be called before any CSRF protected HTTP method
        is called (all HTTP methods of views that extend
        RestView). Returned token must be set in 'X-CSRFToken' header
        when the protected method is called, otherwise the call
        fails. It is enough to get the token once and reuse it for all
        subsequent calls to CSRF protected methods.
        """
        csrf_token = csrf(request).values()[0]
        return HttpResponseJson({'csrfToken': str(csrf_token)})

class Login(RestView):
    """Allows a user to authenticates with BrowserID."""

    def get(self, request):
        """Returns a login page."""
        user = request.user
        if user and user.is_authenticated():
            # If a user is already logged in, show an info page with
            # user's email and a logout link.
            template = loader.get_template('auth/logout.html')
            context = Context({'email' : user.email})
        else:
            template = loader.get_template('auth/login.html')
            context = Context({})
        return HttpResponse(template.render(context))

    def post(self, request, assertion):
        """Logs a user in (establishes a session cookie).

        Verifies BrowserID assertion and check that a user with an
        email verified by the BrowserID is known (added to users
        list)."""
        if assertion == None:
            return HttpResponseBadRequest('BrowserId assertion not set.')
        try:
            user = contrib_auth.authenticate(assertion=assertion)
        except AssertionVerificationException, ex:
            return HttpResponseBadRequest(ex)
        if user is not None:
            contrib_auth.login(request, user)
            logger.debug('%s successfully logged.' % (user.email))
            return HttpResponse("Login successful.")
        else:
            # Return forbidden because request was well formed (400
            # doesn't seem appropriate).
            template = loader.get_template('auth/nothing_shared.html')
            return HttpResponse(template.render(Context({})), status=403)

class Logout(RestView):
    """Allows a user to logout."""

    def get(self, request):
        """Returns a logout page."""
        user = request.user
        if not user.is_authenticated():
            template = loader.get_template('auth/not_authenticated.html')
            return HttpResponse(template.render(Context({})))
        template = loader.get_template('auth/logout.html')
        context = Context({'email' : user.email})
        return HttpResponse(template.render(context))

    def post(self, request):
        """Logs a user out (invalidates a session cookie)."""
        contrib_auth.logout(request)
        template = loader.get_template('auth/bye.html')
        return HttpResponse(template.render(Context({})))


