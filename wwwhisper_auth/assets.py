# wwwhisper - web access control.
# Copyright (C) 2013 Jan Wrobel <jan@mixedbit.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import cache_page
from django.views.generic import View
from wwwhisper_auth import http


class Asset:
    """Stores a static file to be returned by requests."""

    def __init__(self, prefix, *args):
        assert prefix is not None
        self.body = file(os.path.join(prefix, *args)).read()


class StaticFileView(View):
    """ A view to serve a single static file."""

    asset = None

    @method_decorator(cache_control(private=True, max_age=60 * 60 * 5))
    def get(self, request):
        return self.do_get(self.asset.body)

class HtmlFileView(StaticFileView):

    def do_get(self, body):
        return http.HttpResponseOKHtml(body)

class JsFileView(StaticFileView):

    def do_get(self, body):
        return http.HttpResponseOKJs(body)
