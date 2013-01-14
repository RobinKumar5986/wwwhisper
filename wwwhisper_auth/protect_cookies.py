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
    """Sets 'httponly' and (optionally) 'secure' flag for all cookies.

    'httponly' flag protects cookies from JavaScript access.

    'secure' flag prevents cookies from being sent with HTTP
    requests. The flag is set if page is served over HTTPS.
    """

    def process_response(self, request, response):
        for cookie in response.cookies.itervalues():
            cookie['httponly'] = True
            if request.https:
                cookie['secure'] = True
        return response
