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
