(function () {
  'use strict';

  $('#logout').click(function() {
    var stub = new wwwhisper.Stub();
    stub.ajax('POST', '/auth/api/logout/', {}, function() {
      window.location.reload(true);
    });
    return false;
  });
}());
