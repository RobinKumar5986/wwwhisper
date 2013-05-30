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

  /**
   * Sends an assertion from a BrowserID sign-in window to the
   * authentication back-end. Reloads the page if login succeeded.
   */
  function login(assertion) {
    if (assertion) {
      stub.ajax('POST', '/wwwhisper/auth/api/login/',
                { 'assertion' : assertion.toString() },
                function() {
                  window.location.reload(true);
                },
                function(errorMessage, errorStatus) {
                  if (errorStatus === 403) {
                    // Login failed because the user is unknown.
                    $('#login-required').addClass('hide');
                    $('#nothing-shared').removeClass('hide');
                  } else {
                    // Other error.
                    $('body').html(errorMessage);
                  }
                });
    }
  }

  /**
   * Goes to the logout page if the user is already authenticated.
   */
  function gotoLogoutIfAuthenticated() {
    // Whoami succeeds only for authenticated users.
    stub.ajax('GET', '/wwwhisper/auth/api/whoami/', null,
              function() {
                window.location = '/wwwhisper/auth/logout';
              },
              function() {
                // Logget out (errorStatus 401) or some other error.
                // If error was caused by disabled cookies (CSRF token
                // missing), Persona dialog will inform the user how
                // to enable cookies.
              });
  }

  $('#login-required').removeClass('hide');
  $('#login').removeClass('hide');

  // Register a callback to process a BrowserID assertion.
  $('#login').click(function() {
    navigator.id.get(login);
    return false;
  });

  gotoLogoutIfAuthenticated();

}());
