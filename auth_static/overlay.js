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
  stub.setErrorHandler({
    cleanError: function() {},

    handleError: function(message, status) {
      // Remove iframe:
      $('#wwwhisper-iframe', window.parent.document).remove()
    }
  });

  stub.ajax('GET', '/auth/api/whoami/', null,
            function(result) {
              var email;
              email = result.email;
              if (email.length > MAX_EMAIL_LENGTH) {
                // Trim very long emails so 'sign out' button fits in
                // the iframe.
                email = email.substr(0, MAX_EMAIL_LENGTH) + '[...]';
              }
              $('#email').text(email)
              $('#wwwhisper-overlay').removeClass('hidden');
            });
}());
