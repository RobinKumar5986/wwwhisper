[wwwhisper will be released mid-August 2012]

wwwhisper simplifies sharing of Web resources that are not intended
for everyone. It is a generic access control layer for nginx HTTP
server that allows to specify which resources can be accessed by
which visitors.

* wwwhisper grants access to HTTP resources based on users' email
  addresses, which enables sharing with almost every Internet user.
  [Persona](http://persona.org) is used to prove that a visitor owns
  an allowed email, no site-specific password is needed. Persona UI
  makes authentication process really smooth.

* wwwhisper is application independent. It can be used for anything
  that nginx serves - dynamic content, static files, content generated
  by back-end servers. No support from applications or back-ends is needed.

* wwwhisper provides a REST-like API for granting and revoking access
  and an admin web application that gives a convenient UI for
  manipulating permissions. Access to the admin API is protected by
  wwwhisper, this allows to easily authenticate, add and remove admin
  users.



Technical details
-----------------

wwwhisper is a service implemented in Django that should be run along
nginx and that enables following operations:

1. Authentication and authorization: login a user, get an email of
the currently logged in user, logout the user, check if
the user is authorized to access a given location.

2. Admin operations: add/remove a user with a given email, grant a
user access to a given path, revoke access, allow not-authenticated
access to a given path.

wwwhisper utilizes auth-request nginx module created by Maxim Dounin.
The module allows to specify which locations require authorization.
Each time a request is made to a protected location, the auth-request
module sends a sub-request to the wwwhisper process to determines if
the original request should be allowed. The sub-request carries a path
and all headers of the original request (including cookies).
wwwhisper responds to the sub-request in one of three possible ways:

1. If a user is not authenticated (authentication cookie not set or
   invalid), HTTP status code 401 is returned. HTTP server intercepts
   this code and returns a login page to the user.

2. If a user is authenticated and is authorized to access the
   requested resource (user's email is on a list of allowed users),
   sub-request returns HTTP status code 200. HTTP server intercepts
   this code and allows the original request.

3. If a user is authenticated but is not authorized to access the
   requested resource, sub-request returns HTTP status code 403, which
   is returned to the user.

The login page, which is presented to not authenticated users, asks the
user to sign-in with Persona. Sign-in process returns a
cryptographically-secure assertion that is sent to the wwwhisper and that
allows to determine a verified email address of the user. The
assertion does not carry user's password and is valid only for the
current domain, because of this, a malicious site can not use the
assertion to authenticate with other sites. After extracting the email
from the assertion, wwwhisper determines if any resources are shared
with the user. If yes, a session cookie is set and the user is
successfully logged. If no resources are shared, a 403 error is returned
to the user and a session cookie is not set.

nginx sub_filter module is used to insert a small iframe at the bottom
of every protected html document. The iframe contains the user's email
address and a 'sign out' button.


Installation
------------

Following steps demonstrate how to setup nginx with wwwhisper on
Debian-derivative Linux distribution (including Ubuntu). The steps
should be easy to adjust to work on other POSIX systems, if you do so,
please share your experience.

It is strongly recommended to use SSL for protected sites, unless you
are protecting access to something very non-sensitive.

    # Install required packages/
    sudo apt-get install git python-virtualenv libssl-dev supervisor
    # Add a system user to run the wwwhisper service.
    sudo adduser --system --ingroup www-data wwwhisper;
    # Become the user.
    sudo su --shell /bin/bash wwwhisper;
    # Clone wwwhisper project to the wwwhisper home dir.
    cd ${HOME}; git clone https://github.com/wrr/wwwhisper.git .
    # Install wwwhisper dependencies, compile and install nginx with
    # all required modules:
    ./deploy/setup.sh

    # Generate configurations files for a given site. You need to specify
    # your email as admin_email, to be able to access the admin web
    # application.
     ./add_site_config.py --site_url http[s]://domain_of_the_site --admin_email your_email;


Configure nginx. Edit /usr/local/nginx/conf/nginx.conf.  Put

    daemon off

in the top level section, supervisord will be used to daemonize nginx.

Put following directives in the server section:

    set $wwwhisper_static_files_root /home/wwwhisper/www_static/;
    set $wwwhisper_site_socket unix:/home/wwwhisper/sites/$scheme.$server_name.$server_port/uwsgi.sock;
    include /home/wwwhisper/nginx/auth.conf;

Put following directives in the root location section (`location / {`):

    include /home/wwwhisper/nginx/protected_location.conf;
    include /home/wwwhisper/nginx/admin.conf;

It is recommended to make all locations nested in the root location like this:

    location / {
        include /home/wwwhisper/nginx/protected_location.conf;
        include /home//wwwhisper/nginx/admin.conf;

        location /wiki {
            # ...
        }

        location /blog {
            # ...
        }
    }

This ensures all requests are authorized. If for some reason such
setup is not possible, you need to put
     include /home/wwwhisper/nginx/protected_location.conf;

In each location not nested in already protected location, otherwise
requests to the location will be allowed without authentication!

Configure supervisord [to be continued] ...

