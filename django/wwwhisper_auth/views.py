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

logger = logging.getLogger(__name__)

def access_denied_page(email):
    t = loader.get_template('auth/noauthorized.html')
    c = Context({'email' : email})
    return t.render(c)

class Auth(View):
    def get(self, request):
        # TODO: is path encoded by nginx? (e.g. ' ' replaced with %20?).
        path = request.GET.get('path', None)
        if path is None:
            return HttpResponseBadRequest(
                "Auth request should have 'path' paramater.")
        debug_msg = "Auth request to '%s'" % (path)
        user = request.user

        if user and user.is_authenticated():
            debug_msg += " by '%s'" % (user.email)
            if models.can_access(user.email, path):
                logger.debug('%s: access granted.' % (debug_msg))
                return HttpResponse('Access granted.')
            else:
                logger.debug('%s: access denied.' % (debug_msg))
                return HttpResponse(access_denied_page(user.email), status=403)
        else:
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
            template = loader.get_template('auth/nothing_shared.html')
            return HttpResponse(template.render(Context({})), status=403)

class Logout(RestView):
    # TODO: should get be at /auth/api/logout not at /auth/logout?
    def get(self, request):
        user = request.user
        if not user.is_authenticated():
            template = loader.get_template('auth/bye.html')
            return HttpResponse(template.render(Context({})))
        t = loader.get_template('auth/logout.html')
        c = Context({'email' : user.email})
        return HttpResponse(t.render(c))

    def post(self, request):
        contrib_auth.logout(request)
        return HttpResponse('Logged out.')


