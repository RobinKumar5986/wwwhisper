/*!
 * wwwhisper - web access control.
 * Copyright (C) 2012, 2013 Jan Wrobel
 *
 * Licensed under the GPL License version 3 or any later version:
 * https://www.gnu.org/licenses/gpl-3.0.html
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
