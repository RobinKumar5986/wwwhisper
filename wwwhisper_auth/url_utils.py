# wwwhisper - web access control.
# Copyright (C) 2012 Jan Wrobel <wrr@mixedbit.org>
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

"""Functions that operate on an HTTP resource path."""

import posixpath
import urllib
import re
import urlparse

def strip_query(path):
    """Strips query from a path."""
    query_start = path.find('?')
    if query_start != -1:
        return path[:query_start]
    return path

def decode(path):
    """Decodes URL encoded characters in path."""
    return urllib.unquote_plus(path)

def collapse_slashes(path):
    """Replaces repeated path separators ('/') with a single one."""
    return re.sub('//+', '/', path)

def is_canonical(path):
    """True if path is absolute and normalized.

    Canonical path is unique, i.e. two different such paths are never
    equivalent.
    """
    # Posix recognizes '//' as a normalized path, but it is not
    # canonical (it is the same as '/').
    if path == '' or not posixpath.isabs(path) or path.startswith('//'):
        return False
    # Normpath removes trailing '/'.
    normalized_path =  posixpath.normpath(path)
    if (normalized_path != path and normalized_path + '/' != path):
        return False
    return True


def contains_fragment(path):
    """True if path contains fragment id ('#' part)."""
    return path.count('#') != 0

def contains_query(path):
    """True if path contains query string ('?' part)."""
    return path.count('?') != 0

def contains_params(path):
    """True if path contains params (';' part)."""
    return path.count(';') != 0


def validate_site_url(url):
    parsed_url = urlparse.urlparse(url)
    if parsed_url.scheme == '':
        return (False, 'missing scheme (http:// or https://)')
    if parsed_url.scheme not in ('http', 'https'):
        return (False, 'incorrect scheme (should be http:// or https://)')
    if parsed_url.netloc == '':
        return (False, 'missing domain')

    for attr in ['path', 'username', 'query', 'params', 'fragment', 'password']:
        val = getattr(parsed_url, attr, None)
        if val is not None and val != '':
            return (False, 'contains ' + attr)
    return (True, None)

def remove_default_port(url):
    parts = url.split(':')
    if len(parts) != 3:
        return url
    scheme, rest, port = parts
    if ((scheme == 'https' and port == '443') or
        (scheme == 'http' and port == '80')):
        return "%s:%s" % (scheme, rest)
    return url
