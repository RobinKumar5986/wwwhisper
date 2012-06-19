"""Utils to simplify writing of REST style views.

Contains classes representing commonly used HTTP response codes
(similarly to HttpResponseNotFound already available in Django).
"""

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import View

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

    Makes sure a CSRF protection token is passed for each called
    method. Disables caching of responses. For POST and PUT methods,
    deserializes method arguments from a json encoded request body. If
    a specific method is not implemented in a subclass or if is does
    not accept arguments passed in the body, or if some arguments are
    missing, an appropriate error is returned to the client.
    """

    @method_decorator(never_cache)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        """Dispatches a method to a subclass.

        args and kwargs contain arguments that are passed as a query
        string, for PUT and POST these need to be updated with
        arguments passed in a json body.
        """

        method = request.method.lower()
        # Parse body as json object if it is not empty (empty body
        # contains '--BoUnDaRyStRiNg--')
        # TODO: make sure mime type is set to json.
        if (method == 'post' or method == 'put') \
                and len(request.body) != 0 and request.body[0] != '-':
            try:
                # TODO: BUG AHEAD. arguments from the path need to
                # take precedence over arguments from the body,
                # otherwise access control for admin can be
                # circumvented.
                kwargs.update(json.loads(request.body))
            except ValueError, err:
                logger.debug(
                    'Failed to parse request body as json object: %s' % (err))
                return HttpResponseBadRequest(
                    'Failed to parse request body as json object.')
        try:
            return super(RestView, self).dispatch(request, *args, **kwargs)
        except TypeError, err:
            trace = "".join(traceback.format_exc())
            logger.debug('Invalid arguments, handler not found: %s\n%s'
                         % (err, trace))
            return HttpResponseBadRequest('Invalid request arguments')
