(function () {
  'use strict';
  var csrfToken, locations, users, view, refresh;

  csrfToken = null;
  locations = null;
  users = null;

  view = {
    locationPath : null,
    locationInfo : null,
    allowedUser : null,
    addLocation : null,
    user : null,
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

  function allowedUsersEmails(location) {
    return $.map(location.allowedUsers, function(item) {
      return item.email;
    });
  }

  function allLocationsPaths() {
    return extractLocationsPaths(locations);
  }

  function canAccess(userMail, location) {
    return inArray(userMail, allowedUsersEmails(location));
  }

  // TODO: should this be user no userMail?
  function removeAllowedUser(userMail, location) {
    location.allowedUsers = $.grep(location.allowedUsers, function(user) {
      return user.email !== userMail;
    });
  }

  // TODO: fix inconsistent (userMail vs. email)
  function findUser(userMail) {
    var filteredUsers;
    filteredUsers = $.grep(users, function(user) {
      return user.email === userMail;
    });
    if (filteredUsers.length === 0) {
      return null;
    }
    // TODO: assert array has only one element.
    return filteredUsers[0];
  }

  function accessibleLocationsPaths(userMail) {
    var accessibleLocations = $.grep(locations, function(location) {
      return canAccess(userMail, location);
    });
    return extractLocationsPaths(accessibleLocations);
  }

  function locationPathId(locationId) {
    return 'location' + locationId.toString();
  }

  function locationInfoId(locationId) {
    return 'resouce-info' + locationId.toString();
  }

  function findSelectLocationId() {
    return $('#location-list').find('.active').index();
  }

  // TODO: remove duplication.
  function getCsrfToken(successCallback) {
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
  }

  // TODO: Remove this one.
  function ajax(method, resource, params, successCallback) {
    $.ajax({
      url: 'api/' + resource,
      type: method,
      data: JSON.stringify(params),
      //dataType: method === 'GET' ?  'json' : 'text',
      dataType: 'json',
      headers: {'X-CSRFToken' : csrfToken},
      success: successCallback,
      error: function(jqXHR) {
        // TODO: nice messages for user input related failures.
        $('body').html(jqXHR.responseText);
      }
    });
  }

  function ajaxWithUrl(method, resource, params, successCallback) {
    var jsonData = null;
    if (params !== null) {
      jsonData = JSON.stringify(params);
    }

    $.ajax({
      url: resource,
      type: method,
      data: jsonData,
      //dataType: method === 'GET' ?  'json' : 'text',
      dataType: 'json',
      headers: {'X-CSRFToken' : csrfToken},
      success: successCallback,
      error: function(jqXHR) {
        // TODO: nice messages for user input related failures.
        $('body').html(jqXHR.responseText);
      }
    });
  }

  function getLocations() {
    ajax('GET', 'locations/', {}, function(result) {
      // TODO: parse json here.
      locations = result.locations;
      $('.locations-root').text(location.host);
      refresh();
    });
  }

  function getUsers() {
    ajax('GET', 'users/', {}, function(result) {
      // TODO: parse json here.
      users = result.users;
      refresh();
    });
  }

  function addUser(userMail, onSuccessCallback) {
    ajax('POST', 'users/', {email: userMail},
         function(result) {
           users.push(result);
           refresh();
           onSuccessCallback(result);
         });
  }

  function removeUser(user) {
    ajaxWithUrl('DELETE', user.self, null,
         function() {
           $.each(locations, function(locationId, locationValue) {
             if (canAccess(user.email, locationValue)) {
               removeAllowedUser(user.email, locationValue);
             }
           });
           removeFromArray(user, users);
           refresh();
         });
  }

  function urn2uuid(urn) {
    return urn.replace('urn:uuid:', '');
  }

  function allowAccessByUser(userMailArg, locationId) {
    var userMail, userWithMail, location, grantPermissionCallback;
    userMail = $.trim(userMailArg);
    location = locations[locationId];
    if (userMail.length === 0 || canAccess(userMail, location)) {
      return;
    }
    grantPermissionCallback = function(user) {
      ajaxWithUrl('PUT',
                  location.self + 'allowed-users/' + urn2uuid(user.id) + '/',
                  null,
                  function() {
                    location.allowedUsers.push(user);
                    refresh();
                    $('#' + locationInfoId(locationId)
                      + ' ' + '.add-allowed-user').focus();
                  });
    };

    userWithMail = findUser(userMail);
    if (userWithMail !== null) {
      grantPermissionCallback(userWithMail);
    } else {
      addUser(userMail, grantPermissionCallback);
    }
  }

  // TODO: Fix assymetry (locationId above, location here).
  function revokeAccessByUser(user, location) {
    ajaxWithUrl('DELETE',
                location.self + 'allowed-users/' + urn2uuid(user.id) + '/',
                null,
                function() {
                  removeAllowedUser(user.email, location);
                  refresh();
                });
  }

  function addLocation(locationPathArg) {
    var locationPath = $.trim(locationPathArg);
    if (locationPath.length === 0
        || inArray(locationPath, allLocationsPaths())) {
      return;
    }
    ajax('POST', 'locations/', {path: locationPath},
         function(newLocation) {
           // TODO: parse json.
           locations.push(newLocation);
           refresh();
           $('#add-location-input').focus();
         });
  }

  function removeLocation(locationId) {
    ajaxWithUrl('DELETE', locations[locationId].self, null,
         function() {
           locations.splice(locationId, 1);
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
    $.each(locations, function(locationId, locationValue) {
      var id = '#' + locationPathId(locationId);
      if (canAccess(userMail, locationValue)) {
        $(id + ' a').addClass('accessible');
      } else {
        $(id + ' a').addClass('not-accessible');
      }
    });
  }

  function highlighLocationsOff() {
    $('#location-list a').removeClass('accessible');
    $('#location-list a').removeClass('not-accessible');
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
        return 'https://' + location.host + delimiter + locationPath;
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
    // TODO: fix of remove.
    // .typeahead({
    //   'source': model.users
    // })
      .end();

    allowedUserList = locationInfo.find('.allowed-user-list');
    $.each(allowedUsers, function(userIdx, user) {
      view.allowedUser.clone(true)
        .find('.user-mail').text(user.email).end()
        .find('.remove-user').click(function() {
          revokeAccessByUser(user, locations[locationId]);
        }).end()
        .appendTo(allowedUserList);
    });
    locationInfo.appendTo('#location-info-list');
  }

  function showUsers() {
    var user;
    $.each(users, function(userIdx, userListItem) {
      user = view.user.clone(true);
      user.find('.user-mail').text(userListItem.email).end()
        .find('.remove-user').click(function() {
          removeUser(userListItem);
        }).end()
        .find('.highlight').hover(function() {
          highlightAccessibleLocations(userListItem.email);
        }, highlighLocationsOff).end()
        .find('.notify').click(function() {
          showNotifyDialog([userListItem.email],
                           accessibleLocationsPaths(userListItem.email));
        }).end()
        .appendTo('#user-list');
    });
  }

  function showLocations() {
    $.each(locations, function(locationId, locationValue) {
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
        .appendTo('#location-list');
      createLocationInfo(locationId, locationValue.allowedUsers);
    });
    view.addLocation.clone(true)
      .find('#add-location-input')
    // TODO: fix or remove.
    // .typeahead({
    //   'source': allLocationsPaths()
    // })
      .change(function() {
        addLocation($(this).val());
      }).end()
      .appendTo('#location-list');
  }

  refresh = function(selectLocationId) {
    if (typeof selectLocationId === 'undefined') {
      selectLocationId = findSelectLocationId();
    }
    if (selectLocationId === -1) {
      selectLocationId = 0;
    }

    $('#location-list').empty();
    $('#location-info-list').empty();
    $('#user-list').empty();

    showLocations();
    showUsers();

    showLocationInfo(selectLocationId);
  }


  $(document).ready(function() {
    view.locationPath = $('#location-list-item').clone(true);
    view.locationInfo = $('#location-info-list-item').clone(true);
    view.allowedUser = $('#allowed-user-list-item').clone(true);
    view.locationInfo.find('#allowed-user-list-item').remove();
    view.addLocation = $('#add-location').clone(true);
    view.user = $('.user-list-item').clone(true);

    getCsrfToken(function() {
      getLocations();
      getUsers();
    })
  });

}());
