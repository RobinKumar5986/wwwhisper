(function () {
  'use strict';
  // TODO: can this global be removed?
  var csrfToken = null;

  // TODO: remove duplication
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

  function sendAssertion(assertion) {
    if (assertion) {
      ajax('GET', 'csrftoken/', {}, function(result) {
        csrfToken = result.csrfToken;
        ajax('POST', 'verify/', {'assertion' : assertion.toString()},
             function(result) {
               window.location.reload(true);
             });
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
