(function () {
  'use strict';

  var utils = {

    assert: function(condition, message) {
      function AssertionError(message) {
        this.message = message;
        this.toString = function() {
          return 'AssertionError: ' + this.message;
        };
      }

      if (!condition) {
        throw new AssertionError(message);
      }
    },

    each: function(iterable, callback) {
      $.each(iterable, function(id, value) {
        callback(value);
      });
    },

    findOnly: function(array, filterCallback) {
      var result;
      result = $.grep(array, filterCallback);
      if (result.length === 0) {
        return null;
      }
      utils.assert(result.length === 1,
                   'Not unique result of findOnly function.');
      return result[0];
    },

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

    startsWith: function(stringA, stringB) {
      return stringA.lastIndexOf(stringB, 0) === 0;
    },

    urn2uuid: function(urn) {
      return urn.replace('urn:uuid:', '');
    },

    extractLocationsPaths: function(locations) {
      return $.map(locations, function(item) {
        return item.path;
      });
    },

    allowedUsersIds: function(location) {
      return $.map(location.allowedUsers, function(user) {
        return user.id;
      });
    }
  };

  function Controller(UIConstructor, stub) {
    var that = this, ui = new UIConstructor(this);

    this.adminUserEmail = null;
    this.locations = [];
    this.users = [];
    this.adminPath = window.location.pathname;
    this.errorHandler = ui;

    this.canAccess = function(user, location) {
      return location.openAccess || utils.inArray(
        user.id, utils.allowedUsersIds(location));
    };

    this.removeAllowedUser = function(user, location) {
      location.allowedUsers = $.grep(location.allowedUsers, function(u) {
        return u.id !== user.id;
      });
    };

    this.findUserWithEmail = function(email) {
      return utils.findOnly(that.users, function(user) {
        return user.email === email;
      });
    };

    this.findLocationWithId = function(id) {
      return utils.findOnly(that.locations, function(location) {
        return location.id === id;
      });
    };

    this.accessibleLocations = function(user) {
      return $.grep(that.locations, function(location) {
        return that.canAccess(user, location);
      });
    };

    this.getAdminUser = function(nextCallback) {
      stub.setErrorHandler({
        cleanError: function() {},
        handleError: function(message, status) {
          if (status === 401) {
            // TODO: clean this aler.
            alert('Warning...');
            nextCallback();
          } else {
            // Other error.
            $('body').html(message);
          }
        }
      });

      stub.ajax('GET', '/auth/api/whoami/', null, function(result) {
        that.adminUserEmail = result.email;
        stub.setErrorHandler(that.errorHandler);
        nextCallback();
      });
    }

    this.getLocations = function(nextCallback) {
      stub.ajax('GET', 'api/locations/', null, function(result) {
        that.locations = result.locations;
        nextCallback();
      });
    };

    this.getUsers = function(nextCallback) {
      stub.ajax('GET', 'api/users/', null, function(result) {
        that.users = result.users;
        nextCallback();
      });
    };

    this.buildCallbacksChain = function(callbacks) {
      if (callbacks.length === 1) {
        return callbacks[0];
      }
      return function() {
        callbacks[0](
          that.buildCallbacksChain(callbacks.slice(1, callbacks.length))
        );
      };
    };

    this.addLocation = function(locationPathArg) {
      // TODO: do not trim. Spaces are significant.
      var locationPath = $.trim(locationPathArg);
      if (locationPath.length === 0 || utils.inArray(
        locationPath, utils.extractLocationsPaths(that.locations))) {
        // TODO: Should existence check be done by client? Path is
        // encoded anyway on the server site, so this check is not
        // 100% accurate.
        return;
      }
      if (utils.startsWith(locationPath, that.adminPath)) {
        this.errorHandler.handleError(
          'Adding sublocations to admin is not supported '+
            '(It could easily cut off access to the admin application.)');
        return;
      }
      //if (locationPath.
      stub.ajax('POST', 'api/locations/', {path: locationPath},
                function(newLocation) {
                  that.locations.push(newLocation);
                  ui.refresh();
                });
    };

    this.removeLocation = function(location) {
      stub.ajax('DELETE', location.self, null,
        function() {
          utils.removeFromArray(location, that.locations);
          ui.refresh();
        });
    };

    this.addUser = function(emailArg, nextCallback) {
      stub.ajax('POST', 'api/users/', {email: emailArg},
                function(user) {
                  that.users.push(user);
                  nextCallback(user);
                });
    };

    this.removeUser = function(user) {
      stub.ajax('DELETE', user.self, null,
                function() {
                  utils.each(that.locations, function(location) {
                    if (that.canAccess(user, location)) {
                      that.removeAllowedUser(user, location);
                    }
                  });
                  utils.removeFromArray(user, that.users);
                  ui.refresh();
                });
    };

    this.grantOpenAccess = function(location) {
      if (location.openAccess) {
        return;
      }
      stub.ajax(
        'PUT',
        location.self + 'open-access/',
        null,
        function() {
          location.openAccess = true;
          ui.refresh();
        }
      );
    };

    this.revokeOpenAccess = function(location) {
      if (!location.openAccess) {
        return;
      }
      stub.ajax(
        'DELETE',
        location.self + 'open-access/',
        null,
        function() {
          location.openAccess = false;
          ui.refresh();
        }
      );
    };

    this.grantAccess = function(email, location) {
      var cleanedEmail, user, grantPermissionCallback;
      cleanedEmail = $.trim(email);
      if (cleanedEmail.length === 0) {
        return;
      }

      user = that.findUserWithEmail(cleanedEmail);
      if (user !== null && that.canAccess(user, location)) {
        // User already can access location.
        return;
      }

      grantPermissionCallback = function(userArg) {
        stub.ajax(
          'PUT',
          location.self + 'allowed-users/' + utils.urn2uuid(userArg.id) + '/',
          null,
          function() {
            location.allowedUsers.push(userArg);
            ui.refresh();
          });
      };

      if (user !== null) {
        grantPermissionCallback(user);
      } else {
        that.addUser(cleanedEmail, grantPermissionCallback);
      }
    };

    this.revokeAccess = function(user, location) {
      stub.ajax(
        'DELETE',
        location.self + 'allowed-users/' + utils.urn2uuid(user.id) + '/',
        null,
        function() {
          that.removeAllowedUser(user, location);
          ui.refresh();
        });
    };

    this.initialize = function() {
      ui.initialize();
      stub.setErrorHandler(ui);
      that.buildCallbacksChain([that.getAdminUser,
                                that.getLocations,
                                that.getUsers,
                                ui.refresh])();
    };
  }

  function UI(controller) {
    var view = {
      locationPath : null,
      locationInfo : null,
      allowedUser : null,
      addLocation : null,
      user : null,
      errorMessage : null
    }, that = this;

    function userAnnotation(user) {
      if (user.email === controller.adminUserEmail) {
        return ' (you)';
      }
      return '';
    }

    function focusedElement() {
      return $(document.activeElement);
    }

    function locationPathId(location) {
      return 'location-' + utils.urn2uuid(location.id);
    }

    function locationInfoId(location) {
      return 'resource-info-' + utils.urn2uuid(location.id);
    }

    function addAllowedUserInputId(location) {
      return 'add-allowed-user-input-' + utils.urn2uuid(location.id);
    }

    function findSelectLocation() {
      var activeElement, urn;
      activeElement = $('#location-list').find('.active');
      if (activeElement.length === 0) {
        return null;
      }
      urn = activeElement.attr('location-urn');
      return utils.findOnly(controller.locations, function(location) {
        return location.id === urn;
      });
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

    function createLocationInfo(location) {
      var locationInfo, allowedUserList, isAdminLocation, isAdminUser;
      isAdminLocation = (location.path === controller.adminPath);

      locationInfo = view.locationInfo.clone(true)
        .attr('id', locationInfoId(location))
        .attr('location-urn', location.id)
        .find('.add-allowed-user')
        .attr('id', addAllowedUserInputId(location))
        .change(function() {
          var userId = $.trim($(this).val())
          if (userId === '*') {
            controller.grantOpenAccess(location);
          } else {
            controller.grantAccess(userId, location);
          }
        })
      // TODO: fix of remove.
      // .typeahead({
      //   'source': model.users
      // })
        .end();

      allowedUserList = locationInfo.find('.allowed-user-list');
      if (location.openAccess) {
        // TODO: remove mail icon
        view.allowedUser.clone(true)
          .find('.user-mail').text('*').end()
          .find('.unshare').click(function() {
            controller.revokeOpenAccess(location);
          }).end()
          .appendTo(allowedUserList);
      } else {
        utils.each(location.allowedUsers, function(user) {
          isAdminUser = (user.email === controller.adminUserEmail);
          view.allowedUser.clone(true)
            .find('.user-mail').text(user.email + userAnnotation(user)).end()
            .find('.unshare').click(function() {
              controller.revokeAccess(user, location);
            })
             // Protect the current user from disalowing herself
             // access to the admin application.
            .css('visibility',
                 isAdminLocation && isAdminUser ? 'hidden' : 'visible')
            .end()
            .appendTo(allowedUserList);
        });
      }
      locationInfo.appendTo('#location-info-list');
    }

    function highlightAccessibleLocations(user) {
      utils.each(controller.locations, function(location) {
        var id = '#' + locationPathId(location);
        if (controller.canAccess(user, location)) {
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

    function showUsers(selectLocation) {
      var userView, isAdminUser;
      utils.each(controller.users, function(user) {
        userView = view.user.clone(true);
        if (selectLocation !== null &&
            !controller.canAccess(user, selectLocation)) {
          userView.find('.share')
            .removeClass('hide')
            .click(function() {
              controller.grantAccess(user.email, selectLocation);
            });
        }
        isAdminUser = (user.email === controller.adminUserEmail);
        userView.find('.user-mail')
          .text(user.email + userAnnotation(user))
          .end()
          .find('.remove-user').click(function() {
            controller.removeUser(user);
          })
          .css('visibility', isAdminUser ? 'hidden' : 'visible')
          .end()
          .find('.highlight').hover(function() {
            highlightAccessibleLocations(user);
          }, highlighLocationsOff).end()
          .find('.notify').click(function() {
            showNotifyDialog(
              [user.email],
              utils.extractLocationsPaths(
                controller.accessibleLocations(user))
            );
          }).end()
          .appendTo('#user-list');
      });
    }

    function showLocations() {
      var isAdminLocation;
      utils.each(controller.locations, function(location) {
        isAdminLocation = (location.path === controller.adminPath);
        view.locationPath.clone(true)
          .attr('id', locationPathId(location))
          .attr('location-urn', location.id)
          .find('.url').attr(
            'href', '#' + locationInfoId(location)).end()
          .find('.path').text(location.path).end()
          .find('.remove-location').click(function(event) {
            // Do not show removed location info.
            event.preventDefault();
            controller.removeLocation(location);
          })
           // Do not allow admin location to be removed.
          .css('visibility', isAdminLocation ? 'hidden' : 'visible')
          .end()
          .find('.notify').click(function() {
            showNotifyDialog(
              location.allowedUsers, [location.path]);
          }).end()
          .find('.view-page').click(function() {
            window.open(location.path,'_blank');
          }).end()
          .appendTo('#location-list');
        createLocationInfo(location);
      });

      view.addLocation.clone(true)
        .find('#add-location-input')
      // TODO: fix or remove.
      // .typeahead({
      //   'source': utils.allLocationsPaths()
      // })
        .change(function() {
          controller.addLocation($(this).val());
        }).end()
        .appendTo('#location-list');
    }

    function showLocationInfo(location) {
      $('#' + locationPathId(location)).addClass('active');
      $('#' + locationInfoId(location)).addClass('active');
    }

    this.cleanError = function() {
      $('.alert-error').alert('close');
    };

    this.handleError = function(message, status) {
      var error = view.errorMessage.clone(true);

      $('#error-box').empty();
      error.removeClass('hide')
        .find('.alert-message')
        .text(message)
        .end()
        .appendTo('#error-box');

      window.setTimeout(function() {
        error.alert('close');
      }, 5000);
    };

    this.refresh = function() {
      var focusedElementId, selectLocation;
      selectLocation = findSelectLocation();
      focusedElementId = focusedElement().attr('id');

      if (selectLocation === null && controller.locations.length > 0) {
        selectLocation = controller.locations[0];
      }

      $('#location-list').empty();
      $('#location-info-list').empty();
      $('#user-list').empty();

      showLocations();
      showUsers(selectLocation);

      if (selectLocation !== null) {
        showLocationInfo(selectLocation);
      }
      if (focusedElementId) {
        $('#' + focusedElementId).focus();
      }
    };

    this.initialize = function() {
      view.locationPath = $('#location-list-item').clone(true);
      view.locationInfo = $('#location-info-list-item').clone(true);
      view.allowedUser = $('#allowed-user-list-item').clone(true);
      view.locationInfo.find('#allowed-user-list-item').remove();
      view.addLocation = $('#add-location').clone(true);
      view.user = $('.user-list-item').clone(true);
      view.errorMessage = $('.alert-error').clone(true);
      $('.locations-root').text(location.host);

      view.locationPath.find('a').click(function(e) {
        e.preventDefault();
        $(this).tab('show');
        that.refresh();
      });

      // TODO: this is only needed if alert is to be removed programatically.
      $(".alert").alert();

      $('.help').click(function() {
        if ($('.help-message').hasClass('hide')) {
          $('.help-message').removeClass('hide');
          $('.help').text('Hide help');
        } else {
          $('.help-message').addClass('hide');
          $('.help').text('Show help');
        }
      });
    };
  }

  if (window.ExposeForTests) {
    window.utils = utils;
    window.Controller = Controller;
  } else {
    (new Controller(UI, new wwwhisper.Stub())).initialize();
  }
}());
