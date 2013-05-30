/*!
 * wwwhisper - web access control.
 * Copyright (C) 2013 Jan Wrobel
 *
 * Licensed under the GPL License version 3 or any later version:
 * https://www.gnu.org/licenses/gpl-3.0.html
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
