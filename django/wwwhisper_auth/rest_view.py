from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.generic import View

import json

class RestView(View):

    @method_decorator(csrf_protect)
    def dispatch(self, request):
        method = request.method.lower()
        request_args = {}

        if method in self.http_method_names:
            handler = getattr(
                self, method, self.http_method_not_allowed)
            if method != 'get':
                request_args = json.loads(request.raw_post_data)
        else:
            handler = self.http_method_not_allowed

        # TODO: maybe do not pass request?
        return handler(request, **request_args)
