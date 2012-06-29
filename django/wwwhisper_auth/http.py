# wwwhisper - web access control.
# Copyright (C) 2012 Jan Wrobel <wrr@mixedbit.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Utils to simplify writing of REST style views.

Contains classes representing commonly used HTTP response codes
(similarly to HttpResponseNotFound already available in Django).
"""

from django.conf import settings
from django.http import HttpResponse
from django.middleware import csrf
from django.utils.crypto import constant_time_compare
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import View
from wwwhisper_auth import models

import json
import logging
import traceback

logger = logging.getLogger(__name__)


class HttpResponseJson(HttpResponse):
    """"Request succeeded.

    Response contains json representation of a resource.
    """

    def __init__(self, attributes_dict):
        super(HttpResponseJson, self).__init__(json.dumps(attributes_dict),
                                               mimetype="application/json",
                                               status=200)

class HttpResponseNoContent(HttpResponse):
    """Request succeeded but response body is empty."""

    def __init__(self):
        super(HttpResponseNoContent, self).__init__(status=204)

class HttpResponseCreated(HttpResponse):
    """Response returned when resource was created.

    Contains json representation of the created resource.
    """

    def __init__(self, attributes_dict):
        """
        Args:
            attributes_dict: A dictionary containing all attributes of
                the created resource. The attributes are serialized to
                json and returned in the response body
        """

        super(HttpResponseCreated, self).__init__(json.dumps(attributes_dict),
                                                  mimetype="application/json",
                                                  status=201)


class HttpResponseBadRequest(HttpResponse):
    """Response returned when request was invalid."""

    def __init__(self, message):
        logger.debug('Bad request %s' % (message))
        super(HttpResponseBadRequest, self).__init__(message, status=400)

class RestView(View):
    """A common base class for all REST style views.

    Disallows all cross origin requests. Disables caching of
    responses. For POST and PUT methods, deserializes method arguments
    from a json encoded request body. If a specific method is not
    implemented in a subclass, or if it does not accept arguments
    passed in the body, or if some arguments are missing, an
    appropriate error is returned to the client.
    """

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        """Dispatches a method to a subclass.

        kwargs contains arguments that are passed as a query string,
        for PUT and POST arguments passed in a json request body are
        added to kwargs, conflicting names result in an error.
        """

        # Cross-Origin Resource Sharing allows cross origin Ajax GET
        # requests, each such request must have the 'Origin' header
        # set. Drop such requests.
        if request.META.has_key('HTTP_ORIGIN'):
            origin = request.META['HTTP_ORIGIN']
            if origin != models.SITE_URL:
                return HttpResponseBadRequest(
                    'Cross origin requests not allowed.')

        # Validate CSRF token unless test environment disabled CSRF protection.
        if (not getattr(request, '_dont_enforce_csrf_checks', False)
            and not _csrf_token_valid(request)):
            return HttpResponseBadRequest(
                'CSRF token missing or incorrect.')

        method = request.method.lower()
        # Parse body as json object if it is not empty (empty body
        # contains '--BoUnDaRyStRiNg--')
        # TODO: make sure mime type is set to json.
        if (method == 'post' or method == 'put') \
                and len(request.body) != 0 and request.body[0] != '-':
            try:
                if not _utf8_encoded_json(request):
                    return HttpResponseBadRequest(
                        "Invalid Content-Type (only "
                        "'application/json; charset=UTF-8' is acceptable).");

                json_args = json.loads(request.body)
                for k in json_args:
                    if kwargs.has_key(k):
                        return HttpResponseBadRequest(
                            'Invalid argument passed in the request body.')
                    else:
                        kwargs[k] = json_args[k]
                kwargs.update()
            except ValueError as err:
                logger.debug(
                    'Failed to parse the request body a as json object: %s'
                    % (err))
                return HttpResponseBadRequest(
                    'Failed to parse the request body as a json object.')
        try:
            return super(RestView, self).dispatch(request, *args, **kwargs)
        except TypeError as err:
            trace = "".join(traceback.format_exc())
            logger.debug('Invalid arguments, handler not found: %s\n%s'
                         % (err, trace))
            return HttpResponseBadRequest('Invalid request arguments')

def _csrf_token_valid(request):
    """Checks if a valid CSRF token is set in the request header.

    Django CSRF protection middleware is not used directly because it
    allows cross origin GET requests and does strict referer checking
    for HTTPS requests.

    GET request are believed to be safe because they do not modify
    state, but they do require special care to make sure the result is
    not leaked to the calling site. Under some circumstances resulting
    json, when interpreted as script or css, can possibly be
    leaked. The simplest protection is to disallow cross origin GETs.

    Strict referer checking for HTTPS requests is a protection method
    suggested in a study 'Robust Defenses for Cross-Site Request
    Forgery'. According to the study, only 0.2% of users block the
    referer header for HTTPS traffic. Many think the number is low
    enough not to support these users. The methodology used in the
    study had a considerable flaw, and the actual number of users
    blocing the header may be much higher.

    Because all protected methods are called with Ajax, for most
    clients a check that ensures a custom header is set is sufficient
    CSRF protection. No token is needed, because browsers disallow
    setting custom headers for cross origin requests. Unfortunately,
    legacy versions of some plugins did allow such headers. To protect
    users of these plugins a token needs to be used. The problem that
    is left is a protection of a user that is using a legacy plugin in
    a presence of an active network attacker. Such attacker can inject
    his token over HTTP, and exploit the plugin to send the token over
    HTTPS. The impact is mitigated if Strict Transport Security header
    is set (as recommended) for all wwwhisper protected sites (not
    perfect solution, because the header is supported only by the
    newest browsers).
    """
    header_token = request.META.get('HTTP_X_CSRFTOKEN', '')
    cookie_token = request.COOKIES.get(settings.CSRF_COOKIE_NAME, '')
    if (len(header_token) != csrf.CSRF_KEY_LENGTH or
        not constant_time_compare(header_token, cookie_token)):
        return False
    return True

def _utf8_encoded_json(request):
    """Checks if content of the request is defined to be utf8 encoded json.

    'Content-type' header should be set to 'application/json; charset=UTF-8',
    the function allows whitespaces around the two segments.
    """
    content_type = request.META.get('CONTENT_TYPE', '')
    parts = content_type.split(';')
    if (len(parts) != 2 or
        parts[0].strip() != 'application/json' or
        parts[1].strip() != 'charset=UTF-8'):
        return False
    return True
