(function() {
  var mock_stub;

  mock_stub = {
    expectedCalls: [],

    ajax: function(method, resource, params, successCallback) {
      if (this.expectedCalls.length === 0) {
        ok(false, 'Unexpected ajax call ' + method + ' ' + resource);
      } else {
        expectedCall = this.expectedCalls.shift();
        deepEqual(method, expectedCall.method, 'HTTP method' );
        deepEqual(resource, expectedCall.resource, 'HTTP resource');
        deepEqual(params, expectedCall.params, 'HTTP method params');
        successCallback(expectedCall.result);
      }
    },

    expectAjaxCall: function(methodArg, resourceArg, paramsArg, resultArg) {
      this.expectedCalls.push({
        method: methodArg,
        resource: resourceArg,
        params: paramsArg,
        result: resultArg
      });
    },

    verify: function() {
      ok(this.expectedCalls.length == 0, 'All expected ajax calls invoked.')
    },
  };

  wwwhisper.stub = mock_stub;

  wwwhisper.ui = {
    refresh: function() {}
  };

  QUnit.testStart = function() {
    // Reset wwwhisper object state.
    // TODO: Maybe make wwwhisper() a function that return initialized object?
    wwwhisper.locations = [];
    wwwhisper.users = [];
  };

  module('Utility functions');

  test('each', function() {
    sum = 0;
    wwwhisper.utils.each([1, 1, 2, 3, 5], function(x) {
      sum += x;
    });
    deepEqual(sum, 12);
    wwwhisper.utils.each([], function(x) {
      ok(false)
    });
  });

  test('findOnly', function() {
    deepEqual(wwwhisper.utils.findOnly([[1, 2], [2, 3], [4, 5], [5, 6]],
                                       function(x) {
                                         return x[0] == 4;
                                       }), [4, 5]);

    deepEqual(wwwhisper.utils.findOnly([1, 2, 3, 4, 5],
                                       function(x) {
                                         return x == 6;
                                       }), null)
  });

  test('inArray', function() {
    ok(wwwhisper.utils.inArray(2, [1, 2, 3]));
    ok(wwwhisper.utils.inArray('a', ['a', 'b', 'c']));
    ok(wwwhisper.utils.inArray('foo', ['bar', 'baz', 'foo']));
    ok(wwwhisper.utils.inArray('foo', ['foo', 'foo', 'foo']));
    ok(wwwhisper.utils.inArray(true, [true]));

    ok(!wwwhisper.utils.inArray('foo', []));
    ok(!wwwhisper.utils.inArray('foo', ['fooz']));
    ok(!wwwhisper.utils.inArray(1, [[1], 2, 3]));
  });

  test('removeFromArray', function() {
    var array = new Array('aa', 'bb', 'cc');
    wwwhisper.utils.removeFromArray('bb', array);
    deepEqual(array, ['aa', 'cc']);
    wwwhisper.utils.removeFromArray('cc', array);
    deepEqual(array, ['aa']);
    wwwhisper.utils.removeFromArray('a', array);
    deepEqual(array, ['aa']);
    wwwhisper.utils.removeFromArray('aa', array);
    deepEqual(array, []);
    wwwhisper.utils.removeFromArray(null, array);
    deepEqual(array, []);
  });

  test('urn2uuid', function() {
    deepEqual(
      wwwhisper.utils.urn2uuid('urn:uuid:41be0192-0fcc-4a9c-935d-69243b75533c'),
      '41be0192-0fcc-4a9c-935d-69243b75533c');
  });

  test('extractLocationsPaths', function() {
    var result = wwwhisper.utils.extractLocationsPaths([
      {
        id: '12',
        path: '/foo',
      },
      {
        id: '13',
        path: '/foo/bar',
      },
      {
        path: '/baz',
        id: 14,
      }
    ]);
    deepEqual(result, ['/foo', '/foo/bar', '/baz']);
  });

  test('allowedUsersIds', function() {
    deepEqual(wwwhisper.utils.allowedUsersIds(
      {
        id: '12',
        path: '/foo',
        allowedUsers: [
          {
            email: 'foo@example.com',
            id: 'userA'
          },
          {
            email: 'bar@example.com',
            id: 'userB'
          }
        ]
      }), ['userA', 'userB']);

    deepEqual(wwwhisper.utils.allowedUsersIds(
      {
        id: '12',
        path: '/foo',
        allowedUsers: []
      }), []);
  });

  module('locations and users');

  test('canAccess', function() {
    ok(wwwhisper.canAccess(
      {
        id: 'userA',
        email: 'foo@example.com'
      },
      {
        id: '12',
        path: '/foo',
        allowedUsers: [
          {
            email: 'foo@example.com',
            id: 'userA'
          },
          {
            email: 'bar@example.com',
            id: 'userB'
          }
        ]
      }));

    ok(!wwwhisper.canAccess(
      {
        id: 'userC',
        email: 'foo@example.com'
      },
      {
        id: '12',
        path: '/foo',
        allowedUsers: [
          {
            email: 'foo@example.com',
            id: 'userA',
          },
          {
            email: 'bar@example.com',
            id: 'userB',
          }
        ]
      }));
  });

  test('removeAllowedUser', function() {
    var location, userA, userB;
    userA = {
      email: 'foo@example.com',
      id: 'userA'
    };
    userB = {
      email: 'bar@example.com',
      id: 'userB'
    };
    location = {
      id: '12',
      path: '/foo',
      allowedUsers: [
        userA,
        userB,
      ]
    };
    ok(wwwhisper.canAccess(userA, location));
    ok(wwwhisper.canAccess(userB, location));
    wwwhisper.removeAllowedUser(userB, location);
    ok(wwwhisper.canAccess(userA, location));
    ok(!wwwhisper.canAccess(userB, location));
  });

  test('findUserWithEmail', function() {
    var userA, userB;
    userA = {
      email: 'foo@example.com',
      id: 'userA'
    },
    userB = {
      email: 'bar@example.com',
      id: 'userB'
    };
    wwwhisper.users.push(userA);
    wwwhisper.users.push(userB);
    deepEqual(wwwhisper.findUserWithEmail('bar@example.com'), userB);
    deepEqual(wwwhisper.findUserWithEmail('baz@example.com'), null);
  });

  test('accessibleLocations', function() {
    var locationA, locationB, userA, userB, userC;
    userA = {
      email: 'foo@example.com',
      id: 'userA'
    };
    userB = {
      email: 'bar@example.com',
      id: 'userB'
    };
    userC = {
      email: 'baz@example.com',
      id: 'userC'
    };
    wwwhisper.users = [userA, userB, userC];

    locationA = {
      id: '12',
      path: '/foo',
      allowedUsers: [
        userA,
        userB
      ]
    };
    locationB = {
      id: '13',
      path: '/foo/bar',
      allowedUsers: [
        userB
      ]
    };
    wwwhisper.locations = [locationA, locationB];

    deepEqual(wwwhisper.accessibleLocations(userA), [locationA]);
    deepEqual(wwwhisper.accessibleLocations(userB), [locationA, locationB]);
    deepEqual(wwwhisper.accessibleLocations(userC), []);
  });

  module('Ajax calls');

  test('getLocations', function() {
    var ajaxCallResult, callbackCalled;
    ajaxCallResult = {
      locations: [
        {
          path: '/foo',
          id: '1'
        },
        {
          path: '/bar',
          id: '2'
        }
      ]
    };
    callbackCalled = false;
    mock_stub.expectAjaxCall('GET', 'api/locations/', null, ajaxCallResult);
    wwwhisper.getLocations(function() {
      callbackCalled = true;
    });
    deepEqual(wwwhisper.locations, ajaxCallResult.locations);
    ok(callbackCalled);
    mock_stub.verify();
  });

  test('addLocation', function() {
    deepEqual(wwwhisper.locations, []);
    var newLocation = {id: '13', path: '/foo', allowedUsers: []};
    mock_stub.expectAjaxCall('POST', 'api/locations/', {path: '/foo'},
                             newLocation);
    wwwhisper.addLocation('/foo');
    deepEqual(wwwhisper.locations, [newLocation]);
    mock_stub.verify();
  });

  test('addLocation not invoked when location already exists', function() {
    deepEqual(wwwhisper.locations, []);
    // Only single ajax call is expected.
    mock_stub.expectAjaxCall('POST', 'api/locations/', {path: '/foo'},
                             { id: '13', path: '/foo', allowedUsers: []});
    wwwhisper.addLocation('/foo');
    wwwhisper.addLocation('/foo');
    mock_stub.verify();
  });

  test('removeLocation', function() {
    wwwhisper.locations = [{
      id: '13',
      path: '/foo',
      self: 'example.com/locations/13/',
      allowedUsers: [],
    }]
    mock_stub.expectAjaxCall('DELETE', wwwhisper.locations[0].self, null, null);
    wwwhisper.removeLocation(wwwhisper.locations[0]);
    deepEqual(wwwhisper.locations, []);
    mock_stub.verify();
  });

  test('getUsers', function() {
    var ajaxCallResult, callbackCalled;
    ajaxCallResult = {
      users: [
        {
          email: 'foo@example.com',
          id: '1'
        },
        {
          email: 'bar@example.com',
          id: '2'
        }
      ]
    };
    callbackCalled = false;
    mock_stub.expectAjaxCall('GET', 'api/users/', null, ajaxCallResult);
    wwwhisper.getUsers(function() {
      callbackCalled = true;
    });
    deepEqual(wwwhisper.users, ajaxCallResult.users);
    ok(callbackCalled);
    mock_stub.verify();
  });

  test('addUser', function() {
    var nextCallbackInvoked = false;
    deepEqual(wwwhisper.users, []);
    var newUser = {id: '13', email: 'foo@example.com'};
    mock_stub.expectAjaxCall('POST', 'api/users/', {email: 'foo@example.com'},
                             newUser);
    wwwhisper.addUser('foo@example.com',
                      function(userArg) {
                        nextCallbackInvoked = true;
                        deepEqual(userArg, newUser);
                      });
    ok(nextCallbackInvoked);
    deepEqual(wwwhisper.users, [newUser]);
    mock_stub.verify();
  });

  test('removeUser', function() {
    wwwhisper.users = [{
      id: '13',
      email: 'foo@example.com',
      self: 'example.com/users/13/',
    }]
    mock_stub.expectAjaxCall('DELETE', wwwhisper.users[0].self, null, null);
    wwwhisper.removeUser(wwwhisper.users[0]);
    deepEqual(wwwhisper.users, []);
    mock_stub.verify();
  });

  test('removeUser removes from location.allowedUsers list.', function() {
    var location, user;
    user = {
      id: '13',
      email: 'foo@example.com',
      self: 'example.com/users/13/',
    };
    location = {
      id: '17',
      path: '/bar',
      self: 'example.com/locations/13/',
      allowedUsers: [user],
    };
    wwwhisper.users.push(user);
    wwwhisper.locations.push(location);
    mock_stub.expectAjaxCall('DELETE', wwwhisper.users[0].self, null, null);

    ok(wwwhisper.canAccess(user, location));
    wwwhisper.removeUser(wwwhisper.users[0]);
    ok(!wwwhisper.canAccess(user, location));

    deepEqual(location.allowedUsers, []);
    mock_stub.verify();
  });

  test('allowAccess when user exists', function() {
    var location, user;
    user = {
      id: '17',
      email: 'foo@example.com',
      self: 'example.com/users/17/',
    };
    location = {
      id: '13',
      path: '/bar',
      self: 'example.com/locations/13/',
      allowedUsers: [],
    };
    wwwhisper.users.push(user);
    wwwhisper.locations.push(location);
    mock_stub.expectAjaxCall(
      'PUT', location.self + 'allowed-users/17/', null, user);

    ok(!wwwhisper.canAccess(user, location));
    wwwhisper.allowAccessByUser(user.email, location);
    ok(wwwhisper.canAccess(user, location));

    deepEqual(wwwhisper.locations[0].allowedUsers, [user]);
    mock_stub.verify();
  });

  test('allowAccess when user does not exist', function() {
    var location, user;
    user = {
      id: '17',
      email: 'foo@example.com',
      self: 'example.com/users/17/',
    };
    location = {
      id: '13',
      path: '/bar',
      self: 'example.com/locations/13/',
      allowedUsers: [],
    };
    wwwhisper.locations.push(location);
    // User should first be added.
    mock_stub.expectAjaxCall(
      'POST', 'api/users/', {email: 'foo@example.com'}, user);
    mock_stub.expectAjaxCall(
      'PUT', location.self + 'allowed-users/17/', null, user);

    ok(!wwwhisper.canAccess(user, location));
    wwwhisper.allowAccessByUser(user.email, location);
    ok(wwwhisper.canAccess(user, location));

    deepEqual(wwwhisper.locations[0].allowedUsers, [user]);
    deepEqual(wwwhisper.users, [user]);
    mock_stub.verify();
  });

  test('allowAccess when user already can access location', function() {
    var location, user;
    user = {
      id: '17',
      email: 'foo@example.com',
      self: 'example.com/users/17/',
    };
    location = {
      id: '13',
      path: '/bar',
      self: 'example.com/locations/13/',
      allowedUsers: [user],
    };
    wwwhisper.users.push(user);
    wwwhisper.locations.push(location);

    ok(wwwhisper.canAccess(user, location));
    wwwhisper.allowAccessByUser(user.email, location);
    ok(wwwhisper.canAccess(user, location));

    mock_stub.verify();
  });


  test('revokeAccess', function() {
    var location, user;
    user = {
      id: '17',
      email: 'foo@example.com',
      self: 'example.com/users/17/',
    };
    location = {
      id: '13',
      path: '/bar',
      self: 'example.com/locations/13/',
      allowedUsers: [user],
    };
    wwwhisper.users.push(user);
    wwwhisper.locations.push(location);

    mock_stub.expectAjaxCall(
      'DELETE', location.self + 'allowed-users/17/', null, null);

    ok(wwwhisper.canAccess(user, location));
    wwwhisper.revokeAccessByUser(user, location);
    ok(!wwwhisper.canAccess(user, location));

    deepEqual(wwwhisper.locations[0].allowedUsers, []);
    mock_stub.verify();
  });

}());