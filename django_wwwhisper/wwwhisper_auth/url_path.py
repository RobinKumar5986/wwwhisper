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

def strip_query(path):
    """Strips query from a path."""
    query_start = path.find('?')
    if query_start != -1:
        return path[:query_start]
    return path

def decode(path):
    """Decodes URL encoded characters in path."""
    return urllib.unquote_plus(path)

def is_canonical(path):
    """True if path is absolute and normalized.

    Canonical path is unique, i.e. two different such paths are never
    equivalent.
    """
    # Posix recognizes '//' as a normalized path, but it is not
    # canonical (it is the same as '/').
    if path == '' or not posixpath.isabs(path) or path.startswith('//'):
        return False
    # Normpath remove trailing '/'.
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
