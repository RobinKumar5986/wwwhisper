(function () {
  'use strict';
  var wwwhisper;

  // TODO: expose for test.
  function each(iterable, callback) {
    $.each(iterable, function(_id, value) {
      callback(value);
    });
  };

  function findOnly(array, filterCallback) {
    var result;
    result = $.grep(array, filterCallback);
    if (result.length === 0) {
      return null;
    }
    // TODO: assert array has only one element.
    return result[0];
  };

  wwwhisper = {
    csrfToken: null,
    locations: null,
    users: null,

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

    urn2uuid: function(urn) {
      return urn.replace('urn:uuid:', '');
    },

    extractLocationsPaths: function(locations) {
      return $.map(locations, function(item) {
        return item.path;
      });
    },

    allLocationsPaths: function() {
      return wwwhisper.extractLocationsPaths(wwwhisper.locations);
    },

    allowedUsersIds: function(location) {
      return $.map(location.allowedUsers, function(user) {
        return user.id;
      });
    },

    canAccess: function(user, location) {
      return wwwhisper.inArray(
        user.id, wwwhisper.allowedUsersIds(location));
    },

    removeAllowedUser: function(user, location) {
      location.allowedUsers = $.grep(location.allowedUsers, function(u) {
        return u.id !== user.id;
      });
    },

    findUser: function(email) {
      return findOnly(wwwhisper.users, function(user) {
        return user.email === email;
      });
    },

    accessibleLocations: function(user) {
      return $.grep(wwwhisper.locations, function(location) {
        return wwwhisper.canAccess(user, location);
      });
    },

    addAllowedUserInputId: function(location) {
      return 'add-allowed-user-input-' + wwwhisper.urn2uuid(location.id);
    },

    getCsrfToken: function(nextCallback) {
      wwwhisper.stub.ajax('GET', '/auth/api/csrftoken/', {},
                          function(result) {
                            wwwhisper.csrfToken = result.csrfToken;
                            nextCallback();
                          });
    },

    getLocations: function(nextCallback) {
      wwwhisper.stub.ajax('GET', 'api/locations/', {}, function(result) {
        // TODO: parse json here.
        wwwhisper.locations = result.locations;
        nextCallback();
      });
    },

    getUsers: function(nextCallback) {
      wwwhisper.stub.ajax('GET', 'api/users/', {}, function(result) {
        // TODO: parse json here.
        wwwhisper.users = result.users;
        nextCallback();
      });
    },

    buildCallbacksChain: function(callbacks) {
      if (callbacks.length === 1) {
        return callbacks[0];
      }
      return function() {
        callbacks[0](
          wwwhisper.buildCallbacksChain(callbacks.slice(1, callbacks.length))
        );
      }
    },

    addUser: function(userMail, onSuccessCallback) {
      wwwhisper.stub.ajax('POST', 'api/users/', {email: userMail},
                          function(result) {
                            wwwhisper.users.push(result);
                            wwwhisper.ui.refresh();
                            onSuccessCallback();
                          });
    },

    removeUser: function(user) {
      wwwhisper.stub.ajax(
        'DELETE', user.self, null,
        function() {
          each(wwwhisper.locations, function(location) {
            if (wwwhisper.canAccess(user, location)) {
              wwwhisper.removeAllowedUser(user, location);
            }
          });
          wwwhisper.removeFromArray(user, wwwhisper.users);
          wwwhisper.ui.refresh();
        });
    },

    allowAccessByUser: function(email, location) {
      var cleanedEmail, user, location, grantPermissionCallback;
      cleanedEmail = $.trim(email);
      if (cleanedEmail.length === 0) {
        return;
      }
      user = wwwhisper.findUser(cleanedEmail);
      if (user !== null && wwwhisper.canAccess(user, location)) {
        // User already can access location.
        return;
      }

      grantPermissionCallback = function() {
        wwwhisper.stub.ajax(
          'PUT',
          location.self + 'allowed-users/' + wwwhisper.urn2uuid(user.id) + '/',
          null,
          function() {
            location.allowedUsers.push(user);
            wwwhisper.ui.refresh();
          });
      };

      if (user !== null) {
        grantPermissionCallback();
      } else {
        wwwhisper.addUser(cleanedEmail, grantPermissionCallback);
      }
    },

    revokeAccessByUser: function(user, location) {
      wwwhisper.stub.ajax(
        'DELETE',
        location.self + 'allowed-users/' + wwwhisper.urn2uuid(user.id) + '/',
        null,
        function() {
          wwwhisper.removeAllowedUser(user, location);
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
                            wwwhisper.locations.push(newLocation);
                            wwwhisper.ui.refresh();
                          });
    },

    removeLocation: function(location) {
      wwwhisper.stub.ajax(
        'DELETE', location.self, null,
        function() {
          wwwhisper.removeFromArray(location, wwwhisper.locations);
          wwwhisper.ui.refresh();
        });
    },

    initialize: function() {
      wwwhisper.ui.initialize();
      wwwhisper.buildCallbacksChain([wwwhisper.getCsrfToken,
                                     wwwhisper.getLocations,
                                     wwwhisper.getUsers,
                                     wwwhisper.ui.refresh])();
    },
  };

  wwwhisper.ui = {
    view: {
      locationPath : null,
      locationInfo : null,
      allowedUser : null,
      addLocation : null,
      user : null
    },

    _focusedElement: function() {
      return $(document.activeElement);
    },

    _locationPathId: function(location) {
      return 'location-' + wwwhisper.urn2uuid(location.id);
    },

    _locationInfoId: function(location) {
      return 'resource-info-' + wwwhisper.urn2uuid(location.id);
    },

    _findSelectLocation: function() {
      var activeElement, urn;
      activeElement = $('#location-list').find('.active');
      if (activeElement.length === 0) {
        return null;
      }
      urn = activeElement.attr('location-urn');
      return findOnly(wwwhisper.locations, function(location) {
        return location.id === urn;
      });
    },

    _showUsers: function() {
      var userView;
      each(wwwhisper.users, function(user) {
        userView = wwwhisper.ui.view.user.clone(true);
        userView.find('.user-mail').text(user.email).end()
          .find('.remove-user').click(function() {
            wwwhisper.removeUser(user);
          }).end()
          .find('.highlight').hover(function() {
            wwwhisper.ui._highlightAccessibleLocations(user);
          }, wwwhisper.ui._highlighLocationsOff).end()
          .find('.notify').click(function() {
            wwwhisper.ui._showNotifyDialog(
              [user.email],
              wwwhisper.extractLocationsPaths(
                wwwhisper.accessibleLocations(user))
            );
          }).end()
          .appendTo('#user-list');
      });
    },

    _showLocations: function() {
      each(wwwhisper.locations, function(location) {
        wwwhisper.ui.view.locationPath.clone(true)
          .attr('id', wwwhisper.ui._locationPathId(location))
          .attr('location-urn', location.id)
          .find('.url').attr(
            'href', '#' + wwwhisper.ui._locationInfoId(location)).end()
          .find('.path').text(location.path).end()
          .find('.remove-location').click(function(event) {
            // Do not show removed location info.
            event.preventDefault();
            wwwhisper.removeLocation(location);
          }).end()
          .find('.notify').click(function() {
            wwwhisper.ui._showNotifyDialog(
              location.allowedUsers, [location.path]);
          }).end()
          .appendTo('#location-list');
        wwwhisper.ui._createLocationInfo(location);
      });

      wwwhisper.ui.view.addLocation.clone(true)
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

    _showLocationInfo: function(location) {
      $('#' + wwwhisper.ui._locationPathId(location)).addClass('active');
      $('#' + wwwhisper.ui._locationInfoId(location)).addClass('active');
    },

    _createLocationInfo: function(location) {
      var locationInfo, allowedUserList;
      locationInfo = wwwhisper.ui.view.locationInfo.clone(true)
        .attr('id', wwwhisper.ui._locationInfoId(location))
        .attr('location-urn', location.id)
        .find('.add-allowed-user')
        .attr('id', wwwhisper.addAllowedUserInputId(location))
        .change(function() {
          wwwhisper.allowAccessByUser($(this).val(), location);
        })
      // TODO: fix of remove.
      // .typeahead({
      //   'source': model.users
      // })
        .end();

      allowedUserList = locationInfo.find('.allowed-user-list');
      each(location.allowedUsers, function(user) {
        wwwhisper.ui.view.allowedUser.clone(true)
          .find('.user-mail').text(user.email).end()
          .find('.remove-user').click(function() {
            wwwhisper.revokeAccessByUser(user, location);
          }).end()
          .appendTo(allowedUserList);
      });
      locationInfo.appendTo('#location-info-list');
    },

    _highlightAccessibleLocations: function(user) {
      each(wwwhisper.locations, function(location) {
        var id = '#' + wwwhisper.ui._locationPathId(location);
        if (wwwhisper.canAccess(user, location)) {
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


    refresh: function() {
      var focusedElementId, selectLocation;
      selectLocation = wwwhisper.ui._findSelectLocation();
      focusedElementId = wwwhisper.ui._focusedElement().attr('id');

      if (selectLocation === null && wwwhisper.locations.length > 0) {
        selectLocation = wwwhisper.locations[0];
      }

      $('#location-list').empty();
      $('#location-info-list').empty();
      $('#user-list').empty();

      wwwhisper.ui._showLocations();
      wwwhisper.ui._showUsers();

      if (selectLocation !== null) {
        wwwhisper.ui._showLocationInfo(selectLocation);
      }
      if (focusedElementId) {
        $('#' + focusedElementId).focus();
      }
    },

    initialize: function() {
      wwwhisper.ui.view.locationPath = $('#location-list-item').clone(true);
      wwwhisper.ui.view.locationInfo =
        $('#location-info-list-item').clone(true);
      wwwhisper.ui.view.allowedUser = $('#allowed-user-list-item').clone(true);
      wwwhisper.ui.view.locationInfo.find('#allowed-user-list-item').remove();
      wwwhisper.ui.view.addLocation = $('#add-location').clone(true);
      wwwhisper.ui.view.user = $('.user-list-item').clone(true);
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
        headers: {'X-CSRFToken' : wwwhisper.csrfToken},
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
