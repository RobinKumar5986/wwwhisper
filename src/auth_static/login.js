(function () {
  'use strict';

  // http://stackoverflow.com/questions/1403888/get-url-parameter-with-jquery
  function getURLParameter(name) {
    return decodeURI(
        (RegExp(name + '=' + '(.+?)(&|$)').exec(location.search)||[,''])[1]
    );
  }

  $(document).ready(function() {
    $('.site').text(location.host + getURLParameter('next'));
    $('.hidden').removeClass('hidden');
  });

}());
