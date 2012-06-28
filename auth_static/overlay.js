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
                email = email.substr(0, MAX_EMAIL_LENGTH) + '[...]';
              }
              $('#email').text(email)
              $('#wwwhisper-overlay').removeClass('hidden');
            });
}());
