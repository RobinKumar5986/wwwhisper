"""

"""
from django.core.context_processors import csrf
from django.http import HttpResponse
from django.template import Context, loader
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import View
from wwwhisper_auth.backend import AssertionVerificationException;
from wwwhisper_auth.utils import HttpResponseBadRequest
from wwwhisper_auth.utils import RestView
import django.contrib.auth as contrib_auth
import json
import logging
import wwwhisper_auth.models as models
import wwwhisper_auth.url_path as url_path

logger = logging.getLogger(__name__)

def _extract_encoded_path_argument(request):
    request_path_and_args = request.get_full_path()
    assert request_path_and_args.startswith(request.path)
    args = request_path_and_args[len(request.path):]
    if not args.startswith('?path='):
        return None
    return args[len('?path='):]

class Auth(View):
    locations_collection = None

    def get(self, request):
        encoded_path = _extract_encoded_path_argument(request)
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

class CsrfToken(View):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        csrf_token = csrf(request).values()[0]
        json_response = json.dumps({'csrfToken': str(csrf_token)})
        return HttpResponse(json_response, mimetype="application/json")


class Login(RestView):
    def get(self, request):
        user = request.user
        if user and user.is_authenticated():
            # If a user is alredy logged in, show an info page with
            # user's email and a logout link.
            template = loader.get_template('auth/logout.html')
            context = Context({'email' : user.email})
        else:
            template = loader.get_template('auth/login.html')
            context = Context({})
        return HttpResponse(template.render(context))

    def post(self, request, assertion):
        """Process browserid assertions."""
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
            # TODO: Clean the way error is passed to js.
            template = loader.get_template('auth/nothing_shared.html')
            return HttpResponse(template.render(Context({})), status=403)

class Logout(RestView):
    def get(self, request):
        user = request.user
        if not user.is_authenticated():
            template = loader.get_template('auth/not_authenticated.html')
            return HttpResponse(template.render(Context({})))
        t = loader.get_template('auth/logout.html')
        c = Context({'email' : user.email})
        return HttpResponse(t.render(c))

    def post(self, request):
        contrib_auth.logout(request)
        template = loader.get_template('auth/bye.html')
        return HttpResponse(template.render(Context({})))


