/*!
 * wwwhisper - web access control.
 */
(function () {
  'use strict';
  var stub = new wwwhisper.Stub();

  // Make sure a user is authenticated.
  stub.ajax('GET', '/wwwhisper/auth/api/whoami/', null,
            function(result) {
              // Logged in.
              $('#email').text(result.email);
              $('#authenticated').removeClass('hide');
              $('#logout').click(function() {
                stub.ajax(
                  'POST', '/wwwhisper/auth/api/logout/', {}, function() {
                    window.top.location = '/wwwhisper/auth/goodbye.html';
                  });
                return false;
              });
            },
            function(errorMessage, errorStatus) {
              if (errorStatus === 401) {
                $('#authenticated').addClass('hide');
                $('#not-authenticated').removeClass('hide');
              } else {
                // Other error.
                $('body').html(errorMessage);
              }
            });
}());
