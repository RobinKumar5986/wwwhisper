(function () {
  'use strict';
  var csrfToken, locations, users, view, wwwhisper;

  csrfToken = null;
  locations = null;
  users = null;

  view = {
    locationPath : null,
    locationInfo : null,
    allowedUser : null,
    addLocation : null,
    user : null
  };

  wwwhisper = {
    inArray: function(value, array) {
      return ($.inArray(value, array) >= 0);
    },

    removeFromArray: function(value, array) {
      var idx = $.inArray(value, array);
      if (idx === -1) {
        return;
      }
      array.splice(idx, 1);
    },

    extractLocationsPaths: function(locations) {
      return $.map(locations, function(item) {
        return item.path;
      });
    },

    allowedUsersEmails: function(location) {
      return $.map(location.allowedUsers, function(item) {
        return item.email;
      });
    },

    allLocationsPaths: function() {
      return wwwhisper.extractLocationsPaths(locations);
    },

    canAccess: function(userMail, location) {
      return wwwhisper.inArray(
        userMail, wwwhisper.allowedUsersEmails(location));
    },

    // TODO: should this be user no userMail?
    removeAllowedUser: function(userMail, location) {
      location.allowedUsers = $.grep(location.allowedUsers, function(user) {
        return user.email !== userMail;
      });
    },

    // TODO: fix inconsistent (userMail vs. email)
    findUser: function(userMail) {
      var filteredUsers;
      filteredUsers = $.grep(users, function(user) {
        return user.email === userMail;
      });
      if (filteredUsers.length === 0) {
        return null;
      }
      // TODO: assert array has only one element.
      return filteredUsers[0];
    },

    accessibleLocationsPaths: function(userMail) {
      var accessibleLocations = $.grep(locations, function(location) {
        return wwwhisper.canAccess(userMail, location);
      });
      return wwwhisper.extractLocationsPaths(accessibleLocations);
    },

    locationPathId: function(locationId) {
      return 'location' + locationId.toString();
    },

    locationInfoId: function(locationId) {
      return 'resouce-info' + locationId.toString();
    },

    findSelectLocationId: function() {
      return $('#location-list').find('.active').index();
    },

    getCsrfToken: function(successCallback) {
      wwwhisper.stub.ajax('GET', '/auth/api/csrftoken/', {},
                          function(result) {
                            csrfToken = result.csrfToken;
                            successCallback();
                          });
    },

    getLocations: function() {
      wwwhisper.stub.ajax('GET', 'api/locations/', {}, function(result) {
        // TODO: parse json here.
        locations = result.locations;
        wwwhisper.ui.refresh();
      });
    },

    getUsers: function() {
      wwwhisper.stub.ajax('GET', 'api/users/', {}, function(result) {
        // TODO: parse json here.
        users = result.users;
        wwwhisper.ui.refresh();
      });
    },

    addUser: function(userMail, onSuccessCallback) {
      wwwhisper.stub.ajax('POST', 'api/users/', {email: userMail},
                          function(result) {
                            users.push(result);
                            wwwhisper.ui.refresh();
                            onSuccessCallback(result);
                          });
    },

    removeUser: function(user) {
      wwwhisper.stub.ajax(
        'DELETE', user.self, null,
        function() {
          $.each(locations, function(locationId, locationValue) {
            if (wwwhisper.canAccess(user.email, locationValue)) {
              wwwhisper.removeAllowedUser(user.email, locationValue);
            }
          });
          wwwhisper.removeFromArray(user, users);
          wwwhisper.ui.refresh();
        });
    },

    urn2uuid: function(urn) {
      return urn.replace('urn:uuid:', '');
    },

    allowAccessByUser: function(userMailArg, locationId) {
      var userMail, userWithMail, location, grantPermissionCallback;
      userMail = $.trim(userMailArg);
      location = locations[locationId];
      if (userMail.length === 0 || wwwhisper.canAccess(userMail, location)) {
        return;
      }
      grantPermissionCallback = function(user) {
        wwwhisper.stub.ajax(
          'PUT',
          location.self + 'allowed-users/' + wwwhisper.urn2uuid(user.id) + '/',
          null,
          function() {
            location.allowedUsers.push(user);
            wwwhisper.ui.refresh();
            $('#' + wwwhisper.locationInfoId(locationId)
              + ' ' + '.add-allowed-user').focus();
          });
      };

      userWithMail = wwwhisper.findUser(userMail);
      if (userWithMail !== null) {
        grantPermissionCallback(userWithMail);
      } else {
        wwwhisper.addUser(userMail, grantPermissionCallback);
      }
    },

    // TODO: Fix assymetry (locationId above, location here).
    revokeAccessByUser: function(user, location) {
      wwwhisper.stub.ajax(
        'DELETE',
        location.self + 'allowed-users/' + wwwhisper.urn2uuid(user.id) + '/',
        null,
        function() {
          wwwhisper.removeAllowedUser(user.email, location);
          wwwhisper.ui.refresh();
        });
    },

    addLocation: function(locationPathArg) {
      var locationPath = $.trim(locationPathArg);
      if (locationPath.length === 0
          || wwwhisper.inArray(locationPath, wwwhisper.allLocationsPaths())) {
        return;
      }
      wwwhisper.stub.ajax('POST', 'api/locations/', {path: locationPath},
                          function(newLocation) {
                            // TODO: parse json.
                            locations.push(newLocation);
                            wwwhisper.ui.refresh();
                            $('#add-location-input').focus();
                          });
    },

    removeLocation: function(locationId) {
      wwwhisper.stub.ajax(
        'DELETE',
        locations[locationId].self, null,
        function() {
          locations.splice(locationId, 1);
          var selectLocationId = wwwhisper.findSelectLocationId();
          if (selectLocationId === locationId) {
            wwwhisper.ui.refresh(0);
          } else if (selectLocationId > locationId) {
            wwwhisper.ui.refresh(selectLocationId - 1);
          } else {
            wwwhisper.ui.refresh(selectLocationId);
          }
        });
    },

    initialize: function() {
      wwwhisper.ui.initialize();
      wwwhisper.getCsrfToken(function() {
        wwwhisper.getLocations();
        wwwhisper.getUsers();
      });
    }
  };

  wwwhisper.ui = {
    _showUsers: function() {
      var user;
      $.each(users, function(userIdx, userListItem) {
        user = view.user.clone(true);
        user.find('.user-mail').text(userListItem.email).end()
          .find('.remove-user').click(function() {
            wwwhisper.removeUser(userListItem);
          }).end()
          .find('.highlight').hover(function() {
            wwwhisper.ui._highlightAccessibleLocations(userListItem.email);
          }, wwwhisper.ui._highlighLocationsOff).end()
          .find('.notify').click(function() {
            wwwhisper.ui._showNotifyDialog(
              [userListItem.email],
              wwwhisper.accessibleLocationsPaths(userListItem.email));
          }).end()
          .appendTo('#user-list');
      });
    },

    _showLocations: function() {
      $.each(locations, function(locationId, locationValue) {
        view.locationPath.clone(true)
          .attr('id', wwwhisper.locationPathId(locationId))
          .find('.url').attr(
            'href', '#' + wwwhisper.locationInfoId(locationId)).end()
          .find('.path').text(locationValue.path).end()
          .find('.remove-location').click(function(event) {
            // Do not show removed location info.
            event.preventDefault();
            wwwhisper.removeLocation(locationId);
          }).end()
          .find('.notify').click(function() {
            wwwhisper.ui._showNotifyDialog(
              locationValue.allowedUsers, [locationValue.path]);
          }).end()
          .appendTo('#location-list');
        wwwhisper.ui._createLocationInfo(locationId, locationValue.allowedUsers);
      });

      view.addLocation.clone(true)
        .find('#add-location-input')
      // TODO: fix or remove.
      // .typeahead({
      //   'source': allLocationsPaths()
      // })
        .change(function() {
          wwwhisper.addLocation($(this).val());
        }).end()
        .appendTo('#location-list');
    },

    _showLocationInfo: function(locationId) {
      $('#' + wwwhisper.locationPathId(locationId)).addClass('active');
      $('#' + wwwhisper.locationInfoId(locationId)).addClass('active');
    },

    _createLocationInfo: function(locationId, allowedUsers) {
      var locationInfo, allowedUserList;
      locationInfo = view.locationInfo.clone(true)
        .attr('id', wwwhisper.locationInfoId(locationId))
        .find('.add-allowed-user')
        .change(function() {
          wwwhisper.allowAccessByUser($(this).val(), locationId);
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
            wwwhisper.revokeAccessByUser(user, locations[locationId]);
          }).end()
          .appendTo(allowedUserList);
      });
      locationInfo.appendTo('#location-info-list');
    },

    _highlightAccessibleLocations: function(userMail) {
      $.each(locations, function(locationId, locationValue) {
        var id = '#' + wwwhisper.locationPathId(locationId);
        if (wwwhisper.canAccess(userMail, locationValue)) {
          $(id + ' a').addClass('accessible');
        } else {
          $(id + ' a').addClass('not-accessible');
        }
      });
    },

    _highlighLocationsOff: function() {
      $('#location-list a').removeClass('accessible');
      $('#location-list a').removeClass('not-accessible');
    },

    _showNotifyDialog: function(to, locations) {
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
    },


    refresh: function(selectLocationId) {
      if (typeof selectLocationId === 'undefined') {
        selectLocationId = wwwhisper.findSelectLocationId();
      }
      if (selectLocationId === -1) {
        selectLocationId = 0;
      }

      $('#location-list').empty();
      $('#location-info-list').empty();
      $('#user-list').empty();

      wwwhisper.ui._showLocations();
      wwwhisper.ui._showUsers();

      wwwhisper.ui._showLocationInfo(selectLocationId);
    },

    initialize: function() {
      view.locationPath = $('#location-list-item').clone(true);
      view.locationInfo = $('#location-info-list-item').clone(true);
      view.allowedUser = $('#allowed-user-list-item').clone(true);
      view.locationInfo.find('#allowed-user-list-item').remove();
      view.addLocation = $('#add-location').clone(true);
      view.user = $('.user-list-item').clone(true);
      $('.locations-root').text(location.host);
    }
  };

  wwwhisper.stub = {
    ajax: function(method, resource, params, successCallback) {
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
  };

  window.wwwhisper = wwwhisper;
}());
