/*!
 * wwwhisper - web access control.
 * Copyright (C) 2012 Jan Wrobel
 *
 * Licensed under the AGPL License version 3 or any later version:
 * https://www.gnu.org/licenses/agpl-3.0.html
 */
(function () {
  'use strict';
  var stub = new wwwhisper.Stub(), MAX_EMAIL_LENGTH = 30;

  /**
   * Checks if a user is authenticated and if a parent of a current
   * frame is the top level frame (to avoid having several overlays on
   * the screen). If both conditions are true, shows an overlay with
   * the user's email and a 'sign-out' button.
   */


  /**
   * Removes the overlay. Keeping overlay hidden is not enough,
   * because all content below the iframe does not receive
   * user's input (e.g. links are non-clickable).
   */
  function removeOverlay() {
    $('#wwwhisper-iframe', window.parent.document).remove();
  }

  /**
   * Invoked when user is authenticated. Shows the overlay and
   * activates the 'sign-out' button.
   */
  function authenticated(result) {
    var email = result.email;
    if (email.length > MAX_EMAIL_LENGTH) {
      // Trim very long emails so 'sign out' button fits in
      // the iframe.
      email = email.substr(0, MAX_EMAIL_LENGTH) + '[...]';
    }
    $('#email').text(email);
    $('#wwwhisper-overlay').removeClass('hidden');
    $('#logout').click(function() {
      stub.ajax('POST', '/auth/api/logout/', {}, function() {
        window.top.location.reload(true);
      });
    });
  }

  if (window.parent.parent !== window.parent) {
    // Parent is not top level frame.
    removeOverlay();
  } else {
    stub.ajax('GET', '/auth/api/whoami/', null,
              // User is authenticated.
              authenticated,
              // User is not authenticated or some other error occurred.
              removeOverlay);
  }
}());
