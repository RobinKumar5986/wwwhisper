#!/usr/bin/env python

import getopt
import os
import sys
import random
from urlparse import urlparse

SITES_DIR = 'sites'
SETTINGS_DIR = 'settings'
SETTINGS_FILE = 'site_settings.py'
DB_DIR = 'db'
DB_NAME = 'wwwhisper_db'
LOG_DIR = 'log'

def err_quit(errmsg):
    """Prints an error message and quits."""
    print >> sys.stderr, errmsg
    sys.exit(1)

def usage():
    print """

Generates site-specific configuration files. Usage:

  %(prog)s
      -s, --site_url A URL of a site to protect in a form
            scheme://domain(:port). Scheme can be https (recomended) or http.
            Port defaults to 443 for https and 80 for http.
      -a, --admin_email An email of a user that will be allowed to access
            wwwhisper admin interface after wwwhisper is configured.
            More such users can be added via the admin interface.
""" % {'prog': sys.argv[0]}
    sys.exit(1)

def generate_secret_key():
    """Generates a secret key with cryptographically secure generator.

    Displays a warning and generates a key that does not parse if the
    system does not provide a secure generator.
    """
    try:
        secure_generator = random.SystemRandom()
        allowed_chars='abcdefghijklmnopqrstuvwxyz'\
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'\
            '!@#$%^&*(-_=+'
        key_length = 50
        # This gives log2((26+26+10+14)**50) == 312 bits of entropy
        return ''.join(
            [secure_generator.choice(allowed_chars) for i in range(key_length)])
    except NotImplementedError:
        # The system does not support generation of secure random
        # numbers. Return something that raises parsing error and
        # points the user to a place where secret key needs to be
        # filled manually.
        message = ('Your system does not allow to automatically '
                   'generate secure secret keys.')
        print >> sys.stderr, ('WARNING: You need to edit configuration file '
                              'manually. ' + message)
        return ('\'---' + message + ' Replace this text with a long, '
                'unpredictable secret string (at least 50 characters).')


def create_django_settings_file(site_url, admin_email, settings_dir, db_dir):
    """Creates a site specific Django settings file.

    Settings that are common for all sites reside in the
    wwwhisper_service module.
    """

    settings = """
# Don't share this with anybody.
SECRET_KEY = '%s'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '%s',
    }
}

SITE_URL = '%s'
WWWHISPER_ADMINS = ['%s']
""" % (generate_secret_key(),
       os.path.join(db_dir, DB_NAME),
       site_url,
       admin_email)
    init_file_path = os.path.join(settings_dir, '__init__.py')
    settings_file_path = os.path.join(settings_dir, SETTINGS_FILE)
    try:
        with open(init_file_path, 'w') as init_file:
            pass
    except IOError as ex:
        err_quit('Failed to create __init__ file %s: %s.'
                 % (settings_file_path, ex))

    try:
        with open(settings_file_path, 'w') as settings_file:
            settings_file.write(settings)
    except IOError as ex:
        err_quit('Failed to create settings file %s: %s.'
                 % (settings_file_path, ex))

def parse_url(url):
    """Parses and validates a URL.

    URLs need to have scheme://domain:port format, scheme and domain
    are mandatory, port is optional. Terminates the script when URL is
    invalid.
    """

    err_prefix = 'Invalid site address - '
    parsed_url = urlparse(url)
    if parsed_url.scheme == '' or parsed_url.scheme not in ('https', 'http'):
        err_quit(err_prefix + 'scheme missing. '
                 'URL schould start with https:// (recommended) or http://')
    if parsed_url.netloc == '':
        err_quit(err_prefix + 'domain name missing.'
                 'URL should include full domain name (like https://foo.org).')
    if parsed_url.path  != '':
        err_quit(err_prefix + 'URL should not include resource path '
                 '(/foo/bar).')
    if parsed_url.params  != '':
        err_quit(err_prefix + 'URL should not include parameters (;foo=bar).')
    if parsed_url.query  != '':
        err_quit(err_prefix + 'URL should not include query (?foo=bar).')
    if parsed_url.fragment  != '':
        err_quit(err_prefix + 'URL should not include query (#foo).')
    if parsed_url.username != None:
        err_quit(err_prefix + 'URL should not include username (foo@).')
    return (parsed_url.scheme.lower(), parsed_url.netloc.lower())

def main():
    site_url = None
    admin_email = None
    virtualenv_root_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    try:
        optlist, _ = getopt.gnu_getopt(sys.argv[1:],
                                       's:a:h',
                                       ['site_url=', 'admin_email=', 'help'])
    except getopt.GetoptError, ex:
        print 'Arguments parsing error: ', ex,
        usage()

    for opt, arg in optlist:
        if opt in ('-h', '--help'):
            usage()
        elif opt in ('-s', '--site_url'):
            site_url = arg
        elif opt in ('-a', '--admin_email'):
            admin_email = arg
        else:
            assert False, 'unhandled option'


    if site_url is None:
        err_quit('--site_url is missing.')
    if admin_email is None:
        err_quit('--admin_email is missing.')

    (scheme, netloc) = parse_url(site_url)
    config_dir = os.path.join(virtualenv_root_dir, SITES_DIR, scheme, netloc)
    settings_dir = os.path.join(config_dir, SETTINGS_DIR)
    db_dir = os.path.join(config_dir, DB_DIR)
    try:
        os.umask(077)
        os.makedirs(config_dir)
        os.makedirs(settings_dir)
        os.makedirs(db_dir)
        os.makedirs(os.path.join(config_dir, LOG_DIR))
    except OSError as ex:
        err_quit('Failed to initialize configuration directory %s: %s.'
                 % (config_dir, ex))

    create_django_settings_file(scheme + "://" + netloc, admin_email,
                                settings_dir, db_dir)

if __name__ == "__main__":
    main()
