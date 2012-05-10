from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.generic import View

import json
import logging

logger = logging.getLogger(__name__)

class RestView(View):

    @method_decorator(csrf_protect)
    def dispatch(self, request):
        method = request.method.lower()
        request_args = {}

        if method in self.http_method_names:
            handler = getattr(
                self, method, self.http_method_not_allowed)
            if method != 'get':
                try:
                    request_args = json.loads(request.raw_post_data)
                except ValueError, err:
                    logger.debug(
                        'Failed to parse arguments as json object: %s' % (err))
        else:
            handler = self.http_method_not_allowed

        try:
            return handler(request, **request_args)
        except TypeError, err:
            # TODO: test what happens when invalid method is called.
            logger.debug('Invalid arguments, handler not found: %s' % (err))
            return HttpResponse('Invalid request arguments', status=400)
