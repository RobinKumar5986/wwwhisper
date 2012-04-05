(function () {
  'use strict';
  var csrfToken, model, view, refresh;

  csrfToken = null;
  model = null;

  view = {
    locationPath : null,
    locationInfo : null,
    allowedUser : null,
    addLocation : null,
    contact : null,
  };

  function inArray(value, array) {
    return ($.inArray(value, array) >= 0);
  }

  function removeFromArray(value, array) {
    var idx = $.inArray(value, array);
    if (idx === -1) {
      return;
    }
    array.splice(idx, 1);
  }

  function extractLocationsPaths(locations) {
    return $.map(locations, function(item) {
      return item.path;
    });
  }

  function allLocationsPaths() {
    return extractLocationsPaths(model.locations);
  }

  function accessibleLocationsPaths(userMail) {
    var accessibleLocations = $.grep(model.locations, function(location) {
      return inArray(userMail, location.allowedUsers);
    });
    return extractLocationsPaths(accessibleLocations);
  }

  function locationPathId(locationId) {
    return 'location-path' + locationId.toString();
  }

  function locationInfoId(locationId) {
    return 'resouce-info' + locationId.toString();
  }

  function findSelectLocationId() {
    return $('#location-path-list').find('.active').index();
  }

  function mockAjaxCalls() {
    return model !== null && model.mockMode;
  }

  // TODO: remove duplication.
  function getCsrfToken(successCallback) {
    if (!mockAjaxCalls()) {
      $.ajax({
        url: '/auth/api/csrftoken/',
        type: 'GET',
        dataType: 'json',
        success: function(result) {
          csrfToken = result.csrfToken;
          successCallback();
        },
        error: function(jqXHR) {
          $('body').html(jqXHR.responseText);
        }
      })
    } else {
      csrfToken = "mockCsrfToken";
      successCallback();
    }
  }

  function ajax(method, resource, params, successCallback) {
    if (!mockAjaxCalls()) {
      $.ajax({
        url: 'acl/' + resource,
        type: method,
        data: JSON.stringify(params),
        dataType: method === 'GET' ?  'json' : 'text',
        headers: {'X-CSRFToken' : csrfToken},
        success: successCallback,
        error: function(jqXHR) {
          $('body').html(jqXHR.responseText);
        }
      });
    } else {
      successCallback();
    }
  }

  function getModel() {
    ajax('GET', 'model.json', {}, function(result) {
      // TODO: parse json here.
      model = result;
      $('.locations-root').text(model.locationsRoot);
      refresh();
    });
  }

  function addContact(userMail, onSuccessCallback) {
    ajax('PUT', 'contact', {email: userMail},
         function() {
           model.contacts.push(userMail);
           refresh();
           onSuccessCallback();
         });
  }

  function removeContact(userMail) {
    ajax('DELETE', 'contact', {email: userMail},
         function() {
           $.each(model.locations, function(locationId, locationValue) {
             if (inArray(userMail, locationValue.allowedUsers)) {
               removeFromArray(userMail, locationValue.allowedUsers);
             }
           });
           removeFromArray(userMail, model.contacts);
           refresh();
         });
  }

  function allowAccessByUser(userMailArg, locationId) {
    var userMail, location, grantPermissionCallback;
    userMail = $.trim(userMailArg);
    location = model.locations[locationId];
    if (userMail.length === 0
        || inArray(userMail, model.locations[locationId].allowedUsers)) {
      return;
    }
    grantPermissionCallback = function() {
      ajax('PUT', 'permission', {email: userMail,
                                 path: location.path},
           function() {
             location.allowedUsers.push(userMail);
             refresh();
             $('#' + locationInfoId(locationId) + ' ' + '.add-allowed-user')
               .focus();
           });
    };

    if (!inArray(userMail, model.contacts)) {
      addContact(userMail, grantPermissionCallback);
    } else {
      grantPermissionCallback();
    }
  }

  // TODO: Fix assymetry (locationId above, location here).
  function revokeAccessByUser( userMail, location) {
    ajax('DELETE', 'permission', {email: userMail,
                               path: location.path},
           function() {
             removeFromArray(userMail, location.allowedUsers);
             refresh();
           });
  }

  function addLocation(locationPathArg) {
    var locationPath = $.trim(locationPathArg);
    if (locationPath.length === 0
        || inArray(locationPath, allLocationsPaths())) {
      return;
    }
    ajax('PUT', 'location', {path: locationPath},
         function(escapedPath) {
           model.locations.push({
             'path': escapedPath,
             'allowedUsers': []
           });
           refresh();
           $('#add-location-input').focus();
         });
  }

  function removeLocation(locationId) {
    ajax('DELETE', 'location', {path: model.locations[locationId].path},
         function() {
           model.locations.splice(locationId, 1);
           var selectLocationId = findSelectLocationId();
           if (selectLocationId === locationId) {
             refresh(0);
           } else if (selectLocationId > locationId) {
             refresh(selectLocationId - 1);
           } else {
             refresh(selectLocationId);
           }
         });
  }

  function showLocationInfo(locationId) {
    $('#' + locationPathId(locationId)).addClass('active');
    $('#' + locationInfoId(locationId)).addClass('active');
  }

  function highlightAccessibleLocations(userMail) {
    $.each(model.locations, function(locationId, locationValue) {
      var id = '#' + locationPathId(locationId);
      if (inArray(userMail, locationValue.allowedUsers)) {
        $(id + ' a').addClass('accessible');
      } else {
        $(id + ' a').addClass('not-accessible');
      }
    });
  }

  function highlighLocationsOff() {
    $('#location-path-list a').removeClass('accessible');
    $('#location-path-list a').removeClass('not-accessible');
  }

  function showNotifyDialog(to, locations) {
    var body, website, locationsString, delimiter;
    if (locations.length === 0) {
      body = 'I have shared nothing with you. Enjoy.';
    } else {
      website = 'a website';
      if (locations.length > 1) {
        website = 'websites';
      }
      locationsString = $.map(locations, function(locationPath) {
        delimiter = (locationPath[0] !== '/') ? '/' : '';
        return 'https://' + model.locationsRoot + delimiter + locationPath;
      }).join('\n');

      body = 'I have shared ' + website + ' with you.\n'
        + 'Please visit:\n' + locationsString;
    }
    $('#notify-modal')
      .find('#notify-to').attr('value', to.join(', ')).end()
      .find('#notify-body').text(body).end()
      .modal('show');
  }

  function createLocationInfo(locationId, allowedUsers) {
    var locationInfo, allowedUserList;
    locationInfo = view.locationInfo.clone(true)
      .attr('id', locationInfoId(locationId))
      .find('.add-allowed-user')
      .change(function() {
        allowAccessByUser($(this).val(), locationId);
      })
      .typeahead({
        'source': model.contacts
      })
      .end();

    allowedUserList = locationInfo.find('.allowed-user-list');
    $.each(allowedUsers, function(userIdx, userMail) {
      view.allowedUser.clone(true)
        .find('.user-mail').text(userMail).end()
        .find('.remove-user').click(function() {
          revokeAccessByUser(userMail, model.locations[locationId]);
        }).end()
        .appendTo(allowedUserList);
    });
    locationInfo.appendTo('#location-info-list');
  }

  function showContacts() {
    var contact;
    $.each(model.contacts, function(userIdx, userMail) {
      contact = view.contact.clone(true);
      contact.find('.user-mail').text(userMail).end()
        .find('.remove-user').click(function() {
          removeContact(userMail);
        }).end()
        .find('.highlight').hover(function() {
          highlightAccessibleLocations(userMail);
        }, highlighLocationsOff).end()
        .find('.notify').click(function() {
          showNotifyDialog([userMail], accessibleLocationsPaths(userMail));
        }).end()
        .appendTo('#contact-list');
    });
  }

  function showLocations() {
    $.each(model.locations, function(locationId, locationValue) {
      view.locationPath.clone(true)
        .attr('id', locationPathId(locationId))
        .find('.url').attr('href', '#' + locationInfoId(locationId)).end()
        .find('.path').text(locationValue.path).end()
        .find('.remove-location').click(function(event) {
          // Do not show removed location info.
          event.preventDefault();
          removeLocation(locationId);
        }).end()
        .find('.notify').click(function() {
          showNotifyDialog(locationValue.allowedUsers, [locationValue.path]);
        }).end()
        .appendTo('#location-path-list');
      createLocationInfo(locationId, locationValue.allowedUsers);
    });
    view.addLocation.clone(true)
      .find('#add-location-input').typeahead({
        'source': allLocationsPaths()
      })
      .change(function() {
        addLocation($(this).val());
      }).end()
      .appendTo('#location-path-list');
  }

  refresh = function(selectLocationId) {
    if (typeof selectLocationId === 'undefined') {
      selectLocationId = findSelectLocationId();
    }
    if (selectLocationId === -1) {
      selectLocationId = 0;
    }

    $('#location-path-list').empty();
    $('#location-info-list').empty();
    $('#contact-list').empty();

    showLocations();
    showContacts();

    showLocationInfo(selectLocationId);
  }


  $(document).ready(function() {
    view.locationPath = $('#location-path-list-item').clone(true);
    view.locationInfo = $('#location-info-list-item').clone(true);
    view.allowedUser = $('#allowed-user-list-item').clone(true);
    view.locationInfo.find('#allowed-user-list-item').remove();
    view.addLocation = $('#add-location').clone(true);
    view.contact = $('.contact-list-item').clone(true);

    getCsrfToken(getModel);
  });

}());
