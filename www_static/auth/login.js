/*!
 * wwwhisper - web access control.
 */
(function () {
  'use strict';
  var stub = new wwwhisper.Stub();

  /**
   * Sends an assertion from a BrowserID sign-in window to the
   * authentication back-end. Reloads the page if login succeeded.
   */
  function verifyEmail(email) {
    stub.ajax('POST', '/wwwhisper/auth/api/send-token/',
              {'email' : email,
               'path': location.pathname
              },
              function() {
                alert('verifivation email was sent');
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

  // Register a callback to process a BrowserID assertion.
  $('#verify-button').click(function() {
    verifyEmail($('#email-input').val());
  });

  gotoLogoutIfAuthenticated();

}());
