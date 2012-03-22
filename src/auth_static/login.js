(function () {
  'use strict';

  // http://stackoverflow.com/questions/1403888/get-url-parameter-with-jquery
  function getURLParameter(name) {
    return decodeURI(
        (RegExp(name + '=' + '(.+?)(&|$)').exec(location.search)||[,''])[1]
    );
  }


  // http://stackoverflow.com/questions/3846271/
  // jquery-submit-post-synchronously-not-ajax
  function sendAssertion(assertion) {
    if (assertion) {
      $('body').append($('<form/>', {
        id: 'hidden-form',
        method: 'POST',
        action: 'api/browserid/verify/',
      }));

      $('#hidden-form').append($('<input/>', {
        type: 'hidden',
        name: 'assertion',
        value: assertion.toString()
      }));

      $('#hidden-form').append($('<input/>', {
        type: 'hidden',
        name: 'next',
        value: getURLParameter('next')
      }));

      $('#hidden-form').submit();
    } else {
      alert('BrowserID assertion not set');
    }
  }

  $('.site').text(location.host + getURLParameter('next'));
  $('.hidden').removeClass('hidden');
  $('#browserid').click(function() {
    navigator.id.get(sendAssertion);
    return false;
  });
}());
