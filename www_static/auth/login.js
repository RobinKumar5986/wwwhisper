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
                    $('#login-required').addClass('hidden');
                    $('#nothing-shared').removeClass('hidden');
                  } else {
                    // Other error.
                    $('body').html(errorMessage);
                  }
                  // Make sure BrowserId does not retry login.
                  navigator.id.logout();
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
                if (errorStatus === 401) {
                  // Logget out.
                  callback();
                } else {
                  // Other error.
                  $('body').html(errorMessage);
                }
              });
  }

  executeIfLoggedOut(function() {
    $('#login-required').removeClass('hidden');
    $('#login').removeClass('hidden');
    $('#nothing-shared').addClass('hidden');
    // Register a callback to process a BrowserID assertion.
    navigator.id.watch({
      loggedInEmail: null,
      onlogin: login,
      onlogout: function() {}
    });
    $('#login').click(function() {
      navigator.id.request();
      return false;
    });
  });
}());
