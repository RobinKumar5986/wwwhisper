WWWhisper aims to simplify sharing of Web resources with limited
audience. It specifies a generic HTTP access control layer, that
grants access to HTTP resources based on users' emails.  BrowserID
(aka Persona) from Mozilla is used to prove that a visitor owns an
allowed email. WWWhisper is not an application nor a platform. It is
not concerned what the resources are, it can be used to restrict
access to any resource served by HTTP server. The project will provide
a sample implementation of the access control layer and a guidance how
to use it with popular HTTP servers. The project will also provide
[sample UI](http://mixedbit.org/wwwhisper) for granting and revoking
access to web resources.


Introduction
------------

System that allows sharing with limited audience needs to identify
users to ensure only authorized ones can access a protected
resource. Today, the most popular way of identifying allowed audience
are application specific identifiers. This approach enables sharing
only with other users of the application and introduces chicken and
egg dilemma - a new application that enables sharing of private
resources is not very useful, because it has few users, but it won't
have more users until it is useful. Even Facebook, the most popular
application that enables sharing, is very limiting in who you can
share with. Facebook has about 900 million users. This seems a lot,
but it is less than a half of the Internet population, which means if
you need to share something with 10 random Internet users, the chance
that all of them use Facebook is less than one in a thousand (0.5^10).

A better approach is to use open standard of identifying users. There
are several such standards OpenID, WebID, BrowserID. From a point of
view of sharing BrowserID is the best choice, because it is based on
email, which almost every Internet user has. BrowserID allows owner of
even the smallest site to share resources with audience select from
the whole Internet population! Another nice feature of email based ids
is that emails can be used to notify users about shared resources.

Use cases
---------

Lets consider an example of Alice. Alice has following resources to share:

*  A private blog that she would like to share with her family and friends.
*  A work related wiki that she would like to share with her colleagues.
*  A site created for a conference that Alice co-organized.  Alice would
   like the site to be widely accessible, but conference papers should
   be accessible only to conference attendance. In addition all
   organizers should be able to submit photos from the conference.

Alice would like to share resources in a convenient way:

*  She would like to easily grant and revoke access to her sites and check
   who can access what.
*  She wouldn't like anyone to create yet another account and manage yet
   another password to access her sites.
*  She would like to use existing web applications she likes (say WordPress for
   blog and DokuWiki for wiki), but she wouldn't like to do any
   modifications in these applications code.
*  She would like to own the content, be free to move it from server
   server or host it by herself.


HTTP + BrowserID based access control = flexible, open sharing
---------------------------------------------------

The great thing about HTTP protocol is its generality. The protocol
specifies resource identifiers (URLs) and a set methods that can be
performed on resources (GET, POST, PUT, etc.). It does not specify
what resources are and what the methods do, this is left to
applications. To enable flexible sharing, access control layer should
match the level of generality of HTTP. The layer should allow to
specify which users can perform which methods on which resources. This
is the lowest level, that usually won't be exposed to the user that
shares resources, the user will configure access in more granular way
(say specify a set of users that can execute all methods on resources
under a given path).


Technical details
-----------------

A web server Alice uses is configured to authorize access to all
resources within /protected path. Alice uses a generic web application
to grant/revoke access to resources in /protected and to optionally
notify users about shared resources. See [prototype
UI](http://mixedbit.org/wwwhisper) of such application.

Each time the request is made to a protected resource, the web server
makes a sub-request to determine if the original request should be
allowed. The application that serves the sub-requests responds in
three possible ways.

1. If a user is not authenticated (no authentication cookie set), HTTP
   status code 401 is returned. HTTP server intercepts this code and
   redirects the user to a login page, where the user is requested to
   sign-in with BrowserID. [See flow
   diagram](https://github.com/wrr/wwwhisper/raw/master/img/not-authenticated.png)

2. If a user is authenticated and is authorized to access the
   requested resource (user's email is on a list of allowed users),
   sub-request returns HTTP status code 200. HTTP server intercepts
   this code and allows the original request. [See flow
   diagram](https://github.com/wrr/wwwhisper/raw/master/img/authorized.png)

3. If a user is authenticated but is not authorized to access the
   requested resource, sub-request returns HTTP status code 403, which
   is returned to the user. [See flow
   diagram](https://github.com/wrr/wwwhisper/raw/master/img/not-authorized.png)


