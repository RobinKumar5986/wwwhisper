/*!
 * wwwhisper - web access control.
 * Copyright (C) 2012 Jan Wrobel
 *
 * Licensed under the GPL License version 3 or any later version:
 * https://www.gnu.org/licenses/gpl-3.0.html
 */
(function () {
  'use strict';
  var stub = new wwwhisper.Stub();

  // Make sure a user is authenticated.
  stub.ajax('GET', '/auth/api/whoami/', null,
            function(result) {
              // Logged in.
              $('#email').text(result.email);
              $('#authenticated').removeClass('hidden');
              $('#logout').click(function() {
                stub.ajax('POST', '/auth/api/logout/', {}, function() {
                  $('#authenticated').addClass('hidden');
                  $('#logged-out').removeClass('hidden');
                });
                return false;
              });
            },
            function(errorMessage, errorStatus) {
              if (errorStatus === 401) {
                $('#not-authenticated').removeClass('hidden');
              } else {
                // Other error.
                $('body').html(errorMessage);
              }
            });
}());
