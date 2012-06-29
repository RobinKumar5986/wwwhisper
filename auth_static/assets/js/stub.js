/*!
 * wwwhisper - web access control.
 * Copyright (C) 2012 Jan Wrobel
 *
 * Licensed under the AGPL License version 3 or any later version:
 * https://www.gnu.org/licenses/agpl-3.0.html
 */
(function () {
  'use strict';

  function Stub() {
    var csrfToken = null, errorHandler = null, that = this;

    function ajaxCommon(method, resource, params, headersDict,
                        successCallback) {
      if (errorHandler !== null) {
        errorHandler.cleanError()
      }

      if (params === null) {
        $.ajax({
          url: resource,
          type: method,
          headers: headersDict,
          success: successCallback,
          error: function(jqXHR) {
            if (errorHandler !== null) {
              errorHandler.handleError(jqXHR.responseText, jqXHR.status)
            } else {
              // TODO: nice messages for user input related failures.
              $('body').html(jqXHR.responseText);
            }
          }
        });
      } else {
        $.ajax({
          url: resource,
          type: method,
          data: JSON.stringify(params),
          contentType: 'application/json',
          headers: headersDict,
          success: successCallback,
          error: function(jqXHR) {
            if (errorHandler !== null) {
              errorHandler.handleError(jqXHR.responseText, jqXHR.status)
            } else {
              // TODO: nice messages for user input related failures.
              $('body').html(jqXHR.responseText);
            }
          }
        });
      }
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