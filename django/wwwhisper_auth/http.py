from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.views.generic import View

import json
import logging
import traceback

logger = logging.getLogger(__name__)

class HttpResponseBadRequest(HttpResponse):
    def __init__(self, message):
        logger.debug('Bad request %s' % (message))
        super(HttpResponseBadRequest, self).__init__(message, status=400)

class HttpResponseNoContent(HttpResponse):
    def __init__(self):
        super(HttpResponseNoContent, self).__init__(status=204)

class HttpResponseCreated(HttpResponse):
    def __init__(self, json_representation):
        super(HttpResponseCreated, self).__init__(
            json_representation, mimetype="application/json", status=201)

class RestView(View):

    @method_decorator(never_cache)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        method = request.method.lower()
        # Parse body as json object if it is not empty (empty body
        # contains '--BoUnDaRyStRiNg--')
        if (method == 'post' or method == 'put') \
                and len(request.body) != 0 and request.body[0] != '-':
            try:
                kwargs.update(json.loads(request.body))
            except ValueError, err:
                logger.debug(
                    'Failed to parse request body as json object: %s' % (err))
        try:
            return super(RestView, self).dispatch(request, *args, **kwargs)
        except TypeError, err:
            trace = "".join(traceback.format_exc())
            logger.debug('Invalid arguments, handler not found: %s\n%s'
                         % (err, trace))
            return HttpResponse('Invalid request arguments', status=400)
