(function () {
  'use strict';

  function Stub(errorHandler) {
    var csrfToken = null, errorHandler = null, that = this;

    function ajaxCommon(method, resource, params, headersDict,
                        successCallback) {
      var jsonData = null;
      if (params !== null) {
        jsonData = JSON.stringify(params);
      }

      if (errorHandler !== null) {
        errorHandler.cleanError()
      }

      $.ajax({
        url: resource,
        type: method,
        data: jsonData,
        headers: headersDict,
        success: successCallback,
        error: function(jqXHR) {
          if (errorHandler !== null) {
            errorHandler.handleError(jqXHR.responseText)
          } else {
            // TODO: nice messages for user input related failures.
            $('body').html(jqXHR.responseText);
          }
        }
      });
    }

    function getCsrfToken(nextCallback) {
      ajaxCommon('GET', '/auth/api/csrftoken/', null, null,
                 function(result) {
                   csrfToken = result.csrfToken;
                   nextCallback();
                 });
    }

    this.ajax = function(method, resource, params, successCallback) {
      if (csrfToken === null) {
        // Get token and reexecute the call.
        getCsrfToken(function() {
          that.ajax(method, resource, params, successCallback);
        });
        return;
      }
      ajaxCommon(method, resource, params, {'X-CSRFToken' : csrfToken},
                 successCallback);
    };

    this.setErrorHandler = function(handler) {
      errorHandler = handler;
    };
  }

  if (typeof(window.wwwhisper) === 'undefined'){
    window.wwwhisper = {};
  }
  window.wwwhisper.Stub = Stub;
}());