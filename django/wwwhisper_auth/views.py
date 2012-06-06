from django_browserid.base import verify
from django.core.context_processors import csrf
from django.http import HttpResponse
from django.template import Context, loader
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import View
from wwwhisper_auth.utils import HttpResponseBadRequest, RestView
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
        # TODO: login page for logged in users
        t = loader.get_template('auth/login.html')
        return HttpResponse(t.render(Context({})))

    def post(self, request, assertion):
        """Process browserid assertions."""
        if assertion == None:
            return HttpResponseBadRequest('BrowserId assertion not set.')
        result = verify(assertion=assertion, audience=models.SITE_URL)
        print "VERIFIED USER TO BE " + str(result)
        user = contrib_auth.authenticate(assertion=assertion,
                                         audience=models.SITE_URL)
        if user:
            contrib_auth.login(request, user)
            logger.debug('%s successfully logged.' % (user.email))
            return HttpResponse("Login successful.")
        else:
            logger.debug('Login failed (nothing shared with user '
                         'or assertion incorrect).')
            # TODO: show nice 'nothing shared' page here.
            return HttpResponseBadRequest('Login failed')

class Logout(RestView):
    # TODO: should get be at /auth/api/logout not at /auth/logout?
    def get(self, request):
        user = request.user
        if not user.is_authenticated():
            return HttpResponse("Logged out.")
        t = loader.get_template('auth/logout.html')
        c = Context({'email' : user.email})
        return HttpResponse(t.render(c))

    def post(self, request):
        contrib_auth.logout(request)
        return HttpResponse("Logged out")


