import django.contrib.auth as contrib_auth
import string

from django_browserid.auth import get_audience
from django.template import Context, loader
#from django_browserid.context_processors import browserid_form
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.core.context_processors import csrf
from django.views.generic import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
import wwwhisper_auth.acl as acl
#from django_browserid.auth import authenticate

import json

def error(message):
    # TODO: change status.
    return HttpResponse(message, status=400)

class CsrfToken(View):

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        csrf_token = csrf(request).values()[0]
        json_response = json.dumps({'csrfToken': str(csrf_token)})
        return HttpResponse(json_response, mimetype="application/json",
                            status=200)

def auth(request):
    print "HELLLLLLLLLLLLLLLLLOW" + str(request) \
        + " PATH: " + str(request.path) \
        + " METHOD: " + str(request.method) \
        + " COOKIES: " + str(request.COOKIES) \
        + " HOST: " + str(request.get_host())
    user = request.user
    if not request.GET.has_key('uri') and request.GET.has_key('method'):
        # TODO: this gets translated to 500 by nginx
        return error('Incorrect request params')
    path = request.GET['uri']
    method = request.GET['method']
    if user.is_authenticated():
        print "Pieknie. Rozpoznalem usera: " + user.email
        if acl.can_access(user.email, path):
            print "Dostep do " + path + " zezwolony: " + user.email
            return HttpResponse("Hello, world. " + user.email)
        else:
            print "Dostep do " + path + " zabroniony: " + user.email
            response = HttpResponse("Not authorized " + user.email, status=401)
            #TODO which page
            response['X-Error-Msg'] = '%s is not allowed to access this page' % (user.email)
            return response
    else:
        return HttpResponseForbidden('Get out!')


def login(request):
    print "Please login" + str(request)
    t = loader.get_template('auth/login.html')
    return HttpResponse(t.render(Context({})))

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

    @method_decorator(ensure_csrf_cookie)
    def post(self, request):
        contrib_auth.logout(request)
        return HttpResponse("Logged out")



@csrf_protect
@require_POST
def verify(request):
    """Process browserid assertions."""
    print("INVOKEEEEEEEEEEEEEEEEEEEEEEEED")
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
            HttpResponse("User is not active", status=400)
    else:
        print "INVALID FORM"
    return HttpResponse("blebleble", status=400)
