import posixpath
import urllib

def strip_query(path):
    query_start = path.find('?')
    if query_start != -1:
        return path[:query_start]
    return path

def decode(path):
    return urllib.unquote_plus(path)

def is_canonical(path):
    # Posix recognizes '//' as normalized path, but it is not
    # canonical (it is the same as '/').
    if path == '' or not posixpath.isabs(path) or path.startswith('//'):
        return False
    normalized_path =  posixpath.normpath(path)
    if (normalized_path != path and normalized_path + '/' != path):
        return False
    return True


def contains_fragment(path):
    return path.count('#') != 0

def contains_query(path):
    return path.count('?') != 0

def contains_params(path):
    return path.count(';') != 0
