(function () {
  'use strict';
  var stub = new wwwhisper.Stub();
  stub.setErrorHandler({
    cleanError: function() {},

    handleError: function(message, status) {
      if (status === 401) {
        $('#not-authenticated').removeClass('hidden');
      } else {
        // Other error.
        $('body').html(message);
      }
    }
  });

  stub.ajax('GET', '/auth/api/whoami/', null,
            function(result) {
              stub.setErrorHandler(null);
              // Logged in.
              $('#email').text(result.email)
              $('#authenticated').removeClass('hidden');
              $('#logout').click(function() {
                stub.ajax('POST', '/auth/api/logout/', {}, function(message) {
                  $('#authenticated').addClass('hidden');
                  $('#logged-out').removeClass('hidden');
                });
                return false;
              });
            });

}());
