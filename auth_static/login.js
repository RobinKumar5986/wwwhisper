(function () {
  'use strict';

  function sendAssertion(assertion) {
    var stub = new wwwhisper.Stub();
    if (assertion) {
      stub.ajax('POST', '/auth/api/login/',
                {'assertion' : assertion.toString()},
                function() {
                  window.location.reload(true);
                });
    } else {
      alert('BrowserID assertion not set');
    }
  }

  $('#browserid').click(function() {
    navigator.id.get(sendAssertion);
    return false;
  });
}());
