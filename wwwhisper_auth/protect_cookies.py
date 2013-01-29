# wwwhisper - web access control.
# Copyright (C) 2013 Jan Wrobel <wrr@mixedbit.org>
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

class ProtectCookiesMiddleware(object):
    """Sets 'secure' flag for all cookies if request is over https.

    The flag prevents cookies from being sent with HTTP requests.
    """

    def process_response(self, request, response):
        # response.cookies is SimpleCookie (Python 'Cookie' module).
        for cookie in response.cookies.itervalues():
            if request.https:
                cookie['secure'] = True
        return response
