from django.core.context_processors import csrf
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.template import Context, loader
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.views.generic import View
from django_browserid.auth import get_audience
from rest_view import RestView

import django.contrib.auth as contrib_auth
import json
import logging
import wwwhisper_auth.acl as acl

logger = logging.getLogger(__name__)

def error(message):
    logger.debug('error %s' % (message))
    return HttpResponse(message, status=400)

class Auth(View):
    def get(self, request):
        path = request.GET.get('uri', None)
        if path is None:
            return error("Auth request should have 'uri' paramater.")
        debug_msg = "Auth request to '%s'" % (path)
        user = request.user

        if user and user.is_authenticated():
            debug_msg += " by '%s'" % (user.email)
            if acl.can_access(user.email, path):
                logger.debug('%s: access granted.' % (debug_msg))
                return HttpResponse('Access granted.', status=200)
            else:
                logger.debug('%s: access denied.' % (debug_msg))
                return HttpResponse('Access denied', status=401)
        else:
            logger.debug('%s: user not authenticated.' % (debug_msg))
            return HttpResponse('Login required.', status=403)

class CsrfToken(View):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        csrf_token = csrf(request).values()[0]
        json_response = json.dumps({'csrfToken': str(csrf_token)})
        return HttpResponse(json_response, mimetype="application/json",
                            status=200)


class Login(RestView):
    def get(self, request):
        t = loader.get_template('auth/login.html')
        return HttpResponse(t.render(Context({})))

    def post(self, request, assertion):
        """Process browserid assertions."""
        if assertion == None:
            return error('BrowserId assertion not set')
        # TODO: is get_audience here correct?
        user = contrib_auth.authenticate(assertion=assertion,
                                         audience=get_audience(request))
        if user:
            contrib_auth.login(request, user)
            logger.debug('%s successfully logged.' % (user.email))
            return HttpResponse("Login successful.")
        else:
            logger.debug('Login failed (nothing shared with user '
                         'or assertion incorrect).')
            # TODO: show nice 'nothing shared' page here.
            return HttpResponse('Login failed', status=400)

# TODO: Logout -> signout?
class Logout(View):
    #should get be at /auth/api/logout not at /auth/logout
    def get(self, request):
        user = request.user
        if not user.is_authenticated():
            return HttpResponse("Logged out.")
        t = loader.get_template('auth/logout.html')
        c = Context({'email' : user.email})
        return HttpResponse(t.render(c))

    @method_decorator(csrf_protect)
    def post(self, request):
        contrib_auth.logout(request)
        return HttpResponse("Logged out")




def noauthorized(request):
    user = request.user
    # TODO: test this.
    if not user.is_authenticated():
        return login(request)
    t = loader.get_template('auth/noauthorized.html')
    c = Context({'email' : user.email})
    return HttpResponseForbidden(t.render(c))
#    if user.is_authenticated():
#        return HttpResponseForbidden(
#            '%s is not allowed to access this page' % (user.email))
#    else:
#        return HttpResponseForbidden('Get out!')

