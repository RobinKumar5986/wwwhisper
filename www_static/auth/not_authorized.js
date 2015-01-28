/*!
 * wwwhisper - web access control.
 */
(function () {
  'use strict';

  $('#logout').click(function() {
    var stub = new wwwhisper.Stub();

    stub.ajax('POST', '/wwwhisper/auth/api/logout/', {}, function() {
      window.top.location = '/wwwhisper/auth/goodbye.html';
    });
    return false;
  });

}());
