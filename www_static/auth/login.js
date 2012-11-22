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

  /**
   * Sends an assertion from a BrowserID sign-in window to the
   * authentication back-end. Reloads the page if login succeeded.
   */
  function login(assertion) {
    if (assertion) {
      stub.ajax('POST', '/auth/api/login/',
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
   * Executes callback if the user is not authenticated, otherwise
   * takes the user to the logout page.
   */
  function executeIfLoggedOut(callback) {
    // Whoami succeeds only for authenticated users.
    stub.ajax('GET', '/auth/api/whoami/', null,
              function() {
                // Logged in, go to the logout page.
                window.location = '/auth/logout';
              },
              function(errorMessage, errorStatus) {
                // Logget out (errorStatus 401) or some other error.
                // If error was caused by disabled cookies (CSRF token
                // missing), Persona dialog will inform the user how
                // to enable cookies.
                callback();
              });
  }

  executeIfLoggedOut(function() {
    $('#nothing-shared').addClass('hide');
    // Register a callback to process a BrowserID assertion.
    $('#login').click(function() {
      navigator.id.get(login);
      return false;
    });
  });
}());
