(function () {
  'use strict';
  var csrfToken = null;

  function ajax(method, resource, params, successCallback) {
    $.ajax({
      url: '/auth/api/' + resource,
      type: method,
      data: JSON.stringify(params),
      dataType: method === 'GET' ?  'json' : 'text',
      headers: csrfToken != null ? {'X-CSRFToken' : csrfToken}: {},
      success: successCallback,
      error: function(jqXHR) {
        $('body').html(jqXHR.responseText);
      }
    });
  }


  $('#logout').click(function() {
    ajax('GET', 'csrftoken/', {}, function(result) {
      csrfToken = result.csrfToken;
      ajax('POST', 'logout/', {}, function(result) {
        window.location.reload(true);
      });
    });
    return false;
  });
}());
