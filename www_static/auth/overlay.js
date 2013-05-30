/*!
 * wwwhisper - web access control.
 * Copyright (C) 2012, 2013 Jan Wrobel
 *
 * Licensed under the GPL License version 3 or any later version:
 * https://www.gnu.org/licenses/gpl-3.0.html
 */

/**
 * If the user is authenticated, shows an overlay with the user's
 * email and a 'sign-out' button.
 */
(function () {
  'use strict';
  var stub = new wwwhisper.Stub(), MAX_EMAIL_LENGTH = 30;

  /**
   * Removes the overlay. Keeping overlay hidden is not enough,
   * because all content below the iframe does not receive
   * user's input (e.g. links are non-clickable).
   */
  function removeOverlay() {
    $('#wwwhisper-iframe', window.parent.document).remove();
  }

  function logoutSucceeded() {
    window.top.location = '/wwwhisper/auth/goodbye.html';
  }

  function logout() {
    stub.ajax('POST', '/wwwhisper/auth/api/logout/', {}, logoutSucceeded);
  }

  function authenticated(result) {
    var emailToDisplay = result.email;
    if (emailToDisplay.length > MAX_EMAIL_LENGTH) {
      // Trim very long emails so 'sign out' button fits in
      // the iframe.
      emailToDisplay = result.email.substr(0, MAX_EMAIL_LENGTH) + '[...]';
    }
    $('#email').text(emailToDisplay);
    $('#wwwhisper-overlay').removeClass('hide');
    $('#logout').click(logout);
  }

  stub.ajax('GET', '/wwwhisper/auth/api/whoami/', null,
            // User is authenticated.
            authenticated,
            // User is not authenticated or some other error occurred.
            removeOverlay);
}());
