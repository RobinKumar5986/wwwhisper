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


class Login(View):
    def get(self, request):
        #print "Please login" + str(request)
        t = loader.get_template('auth/login.html')
        return HttpResponse(t.render(Context({})))

    @method_decorator(csrf_protect)
    def post(self, request):
        """Process browserid assertions."""
        print("verify assertion")
        # redirect_to = request.REQUEST.get(redirect_field_name, '')
        # if not redirect_to:
        #     redirect_to = getattr(settings, 'LOGIN_REDIRECT_URL', '/')
        # redirect_to_failure = getattr(settings, 'LOGIN_REDIRECT_URL_FAILURE', '/')
    #print("validating from")
        request_args = json.loads(request.raw_post_data)
        assertion = request_args['assertion']
    #form = BrowserIDForm(data=request.POST)
    #print("from validation done")
    # TODO: can it be None?
        if assertion != None:
        #assertion = form.cleaned_data['assertion']
            print "Authenticating user"
            user = contrib_auth.authenticate(assertion=assertion,
                                             audience=get_audience(request))
            print "user authenticated "
            if user is not None and user.is_active:
                contrib_auth.login(request, user)
                return HttpResponse("Login ok")
            else:
            # TODO: test this.
                print "User " + str(user) + " is not active."
                return HttpResponse("User is not active", status=400)
        else:
            print "assertion not set"
        return HttpResponse("assertion not set", status=400)

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

