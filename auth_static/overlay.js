/*!
 * wwwhisper - web access control.
 * Copyright (C) 2012 Jan Wrobel
 *
 * Licensed under the AGPL License version 3 or any later version:
 * https://www.gnu.org/licenses/agpl-3.0.html
 */
(function () {
  'use strict';
  var MAX_EMAIL_LENGTH = 30;
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

  if (window.parent.parent !== window.parent) {
    // Parent is not top level frame.
    removeOverlay();
  } else {
    (new wwwhisper.Stub())
      .ajax('GET', '/auth/api/whoami/', null,
            function(result) {
              var email;
              email = result.email;
              if (email.length > MAX_EMAIL_LENGTH) {
                // Trim very long emails so 'sign out' button fits in
                // the iframe.
                email = email.substr(0, MAX_EMAIL_LENGTH) + '[...]';
              }
              $('#email').text(email);
              $('#wwwhisper-overlay').removeClass('hidden');
            },
            // User is not authenticated or some other error occurred.
            removeOverlay);
  }
}());
