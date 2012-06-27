(function () {
  'use strict';
  var stub = new wwwhisper.Stub();

  function login(assertion) {
    if (assertion) {
      stub.setErrorHandler({
        cleanError: function() {},

        handleError: function(message, status) {
          if (status === 403) {
            // Login failed because user is unknown.
            $('#sign-in').addClass('hidden');
            $('#nothing-shared').removeClass('hidden');
          } else {
            // Other error.
            $('body').html(message);
          }
        }
      });

      stub.ajax('POST', '/auth/api/login/',
                { 'assertion' : assertion.toString() },
                function() {
                  window.location.reload(true);
                });
    } else {
      alert('BrowserID assertion not set');
    }
  }

  function executeIfLoggedOut(callback) {
    stub.setErrorHandler({
      cleanError: function() {},

      handleError: function(message, status) {
        if (status === 401) {
          // Logget out.
          callback();
        } else {
          // Other error.
          $('body').html(message);
        }
      }
    });

    stub.ajax('GET', '/auth/api/whoami/', null,
              function(result) {
                // Logged in, go to the logout page.
                window.location = '/auth/logout.html';
              });
  }

  executeIfLoggedOut(function() {
    $('#sign-in').removeClass('hidden');
    $('#browserid').removeClass('hidden');
    $('#nothing-shared').addClass('hidden');
    $('#browserid').click(function() {
      navigator.id.get(login);
      return false;
    });
  });

}());
