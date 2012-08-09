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

Quick tour
-----------

Upon visiting a wwwhisper protected site, a user is presented with a
login prompt:

![Login prompt](https://raw.github.com/wrr/www/master/mixedbit.org/wwwhisper_screens/login_required.png)

'Sign in' button opens Mozilla Persona authentication dialog. Persona
alows the user to smoothly and securely verify that she owns a
given email address:

![Login prompt](https://raw.github.com/wrr/www/master/mixedbit.org/wwwhisper_screens/persona_dialog.png)

After successful authentication, wwwhisper checks that the user is
allowed to visit a given site. If this is the case, the user is taken
to the site:

![Access granted](https://raw.github.com/wrr/www/master/wwwhisper_screens/access_granted.png)

Usually web authentication systems are built into web
applications. With wwwhisper this is not required. The photo album
above consist of static html and javascript files with no dynamic code
executed at the server side and with no awerness of wwwhisper.

Nginx inserts a small overlay in the lower-right corner of each
protected html document. The overlay contains an email of the current
user and a 'Sign out' button.

If the user visits a location that she is not allowed to access, an
error is displayed:
![Access denied](https://raw.github.com/wrr/www/master/wwwhisper_screens/access_denied.png)

Finally, the admin application allows to easily grant and revoke
access and to check who can access what. It also helps to compose
invitations emails to allowed users:

![Admin](https://raw.github.com/wrr/www/master/wwwhisper_screens/admin.png)

All the site admins need to do, is to specify emails of allowed
users. There is no need to create, distribute and manage
passwords. Also, unlike in cases of URL encoded credentials, URLs of
protected sites to not need to be kept private. If someone discovers
such URL, he won't be able to access the resource without
authenticating with an allowed email.

Technical details
-----------------

wwwhisper is a service implemented in Django that runs along nginx
and that enables following actions:

1. Authentication and authorization: login a user, get an email of
the currently logged in user, logout the user, check if
the user is authorized to access a given location.

2. Admin operations: add/remove a user with a given email, grant a
user access to a given path, revoke access, allow not-authenticated
access to a given path.

wwwhisper utilizes auth-request nginx module created by Maxim Dounin.
The module allows to specify which locations require authorization.
Each time a request is made to a protected location, the auth-request
module sends a sub-request to the wwwhisper process to determine if
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

The login page, which is presented to not authenticated users, asks
the user to sign-in with Persona. Sign-in process returns a
cryptographically-secure assertion that is sent to the wwwhisper and
that allows to determine a verified email address of the user. The
assertion does not carry user's password and is valid only for the
current domain, because of this, a malicious site can not use the
assertion to authenticate with other sites. After extracting the email
from the assertion, wwwhisper determines if any resources are shared
with the user. If yes, a session cookie is set and the user is
successfully logged in. If no resources are shared, a 403 error is
returned to the user and a session cookie is not set.

nginx sub_filter module is used to insert a small iframe at the bottom
of every protected html document. The iframe contains the user's email
address and a 'sign out' button.


Setup
-----

Following steps demonstrate how to install and configure nginx with
wwwhisper authentication on Debian-derivative distributions (including
Ubuntu). The steps should be easy to adjust to work on other POSIX
systems. [Unprivileged
installation](https://github.com/wrr/wwwhisper/blob/master/doc/unprivileged_install.md)
is good for experiments, development or if you don't have
administrative priviledged on the machine. [System-wide
installation](https://github.com/wrr/wwwhisper/blob/master/doc/system_wide_install.md)
is recommended for more serious deployments.

If you are already using nginx or uwsgi, you may use these steps only
as guidance and adjust them to fit your current configuration.

Final remarks
-----------------

1. Make sure content you are protecting can not be accessed through
some other channels. If you are using a multiuser server, set
correct file permissions for protected static files and
communication sockets. If nginx is delegating requests to backend
servers, make sure the backends are not externally accessible.

2. Use SSL for anything important. You can get a free [SSL certificate
   for personal use](https://cert.startcom.org/).