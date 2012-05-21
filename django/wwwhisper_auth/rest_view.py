from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.generic import View

import json
import logging
import traceback

logger = logging.getLogger(__name__)

class RestView(View):

    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        method = request.method.lower()
        # TODO: remove delete
        if method == 'post' or method == 'put':
            try:
                kwargs.update(json.loads(request.raw_post_data))
            except ValueError, err:
                logger.debug(
                    'Failed to parse arguments as json object: %s' % (err))
        try:
            return super(RestView, self).dispatch(request, *args, **kwargs)
        except TypeError, err:
            # TODO: test that this is called
            # TODO: test what happens when invalid method is called.
            trace = "".join(traceback.format_exc())
            logger.debug('Invalid arguments, handler not found: %s\n%s'
                         % (err, trace))
            # TODO: change error code.
            return HttpResponse('Invalid request arguments', status=400)
