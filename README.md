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


Installation
------------

Following steps demonstrate how to setup nginx with wwwhisper on
Debian-derivative Linux distribution (including Ubuntu). The steps
should be easy to adjust to work on other POSIX systems.

### Install required packages.

    sudo apt-get install git python-virtualenv libssl-dev;

### Get, compille and install nginx.
    # Download and unpack the latest stable nginx.
    NGINX_VERSION='nginx-1.2.3';
    mkdir ~/src; cd ~/src;
    wget http://nginx.org/download/${NGINX_VERSION}.tar.gz;
    tar xvfz ${NGINX_VERSION}.tar.gz;
    cd ${NGINX_VERSION};
    # Get auth-request module.
    git clone https://github.com/PiotrSikora/ngx_http_auth_request_module.git;
    # Configure nginx. If your site needs any additonal modules add them here.
    # Also, it you want to install nginx in a different directory,
    # modify --prefix and --sbin-path
    ./configure --add-module=./ngx_http_auth_request_module/ \
      --with-http_ssl_module --with-http_sub_module --user=www-data \
      --group=www-data --prefix=/usr/local/nginx/ --sbin-path=/usr/local/sbin
    # Compile and install nginx.
    make; sudo make install;

### Install wwwhisper
    # Add a system user to run the wwwhisper service.
    sudo adduser --system --ingroup www-data wwwhisper;
    # Become the user.
    cd ~wwwhisper; sudo su --shell /bin/bash wwwhisper;
    # Clone wwwhisper project to the wwwhisper home dir.
    git clone https://github.com/wrr/wwwhisper.git .;
    # Create and activate virtual environment.
    virtualenv virtualenv;
    source virtualenv/bin/activate;
    # Install packages required in the virtual environment.
    pip install -r ./requirements.txt;
    # Generate configurations files for a site to protect. You need to
    # specify your email as admin_email, to be able to access the
    # admin web application. This step can be later repeated to enable
    # protection for multiple sites.
    ./add_site_config.py --site_url  http[s]://domain_of_the_site[:port] --admin_email your@email;

### Configure nginx
Edit /usr/local/nginx/conf/nginx.conf and enable wwwhisper
authorization.  See [a sample configuration
file](https://github.com/wrr/wwwhisper/blob/master/nginx/sample_nginx.conf)
that explains all wwwhisper configuration related directives. In
particular, pay attention to following directives:

    user www-data www-data;
    daemon off;

    set $wwwhisper_root /home/wwwhisper/;
    set $wwwhisper_site_socket unix:$wwwhisper_root/sites/$scheme.$server_name.$server_port/uwsgi.sock;
    include /home/wwwhisper/nginx/auth.conf;

    include /home/wwwhisper/nginx/protected_location.conf;
    include /home/wwwhisper/nginx/admin.conf;

### Configure supervisor

Supervisord can be used to automatically start nginx and uwsgi managed
wwwhisper process. Alternatively you can use a little harder to
configure [init.d scripts](http://wiki.nginx.org/Nginx-init-ubuntu).

     sudo apt-get install supervisor;

 Edit /etc/supervisor/supervisord.conf and extend existing include directive to include `/home/wwwhisper/sites/*/supervisor/site.conf` and `/home/wwwhisper/nginx/supervisor.conf`. The directive should now look something like:

    [include]
    files = /etc/supervisor/conf.d/*.conf /home/wwwhisper/sites/*/supervisor/site.conf /home/wwwhisper/nginx/supervisor.conf

Note that supervisord does not allow multiple include directives, you need to extend the existing one.

Finally, restart the supervisor

    sudo /etc/init.d/supervisor stop; \
    sleep 20; \
    sudo /etc/init.d/supervisor start;

Point your browser to http[s]://your.site.address/admin, you should be
presented with a login page. Sign in with your email and use the admin
application to define which locations can be accessed by which
visitor.

Final remarks
-----------------

1. Make sure content you are protecting can not be accessed through
some other channels. If you are using a multiuser server, set
correct file permissions for protected static files and
communication sockets. If nginx is delegating requests to backend
servers, make sure the backends are not externally accessible.

2. Use SSL for anything important. You can get a free [SSL certificate
   for personal use](https://cert.startcom.org/).