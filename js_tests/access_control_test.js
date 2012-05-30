(function() {
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
      if (this.expectedCalls.length !== 0) {
        ok(false, 'Expected ajax call not invoked: '
           + this.expectedCalls[0].method
           + ' ' + this.expectedCalls[0].resource);
      }
    }
  };

  wwwhisper.stub = mock_stub;

  wwwhisper.ui = {
    refresh: function() {}
  };

  QUnit.testStart = function() {
    mock_stub.verify();
    // Reset wwwhisper object state.
    // TODO: Maybe make wwwhisper() a function that return initialized object?
    wwwhisper.locations = [];
    wwwhisper.users = [];
  };

  module('Utility functions');

  test('inArray', function() {
    ok(wwwhisper.inArray(2, [1, 2, 3]));
    ok(wwwhisper.inArray('a', ['a', 'b', 'c']));
    ok(wwwhisper.inArray('foo', ['bar', 'baz', 'foo']));
    ok(wwwhisper.inArray('foo', ['foo', 'foo', 'foo']));
    ok(wwwhisper.inArray(true, [true]));

    ok(!wwwhisper.inArray('foo', []));
    ok(!wwwhisper.inArray('foo', ['fooz']));
    ok(!wwwhisper.inArray(1, [[1], 2, 3]));
  });

  test('removeFromArray', function() {
    var array = new Array('aa', 'bb', 'cc');
    wwwhisper.removeFromArray('bb', array);
    deepEqual(array, ['aa', 'cc']);
    wwwhisper.removeFromArray('cc', array);
    deepEqual(array, ['aa']);
    wwwhisper.removeFromArray('a', array);
    deepEqual(array, ['aa']);
    wwwhisper.removeFromArray('aa', array);
    deepEqual(array, []);
    wwwhisper.removeFromArray(null, array);
    deepEqual(array, []);
  });

  test('urn2uuid', function() {
    deepEqual(
      wwwhisper.urn2uuid('urn:uuid:41be0192-0fcc-4a9c-935d-69243b75533c'),
      '41be0192-0fcc-4a9c-935d-69243b75533c');
  });

  test('extractLocationsPaths', function() {
    var result = wwwhisper.extractLocationsPaths([
      {
        id: 12,
        path: '/foo',
      },
      {
        id: 13,
        path: '/foo/bar',
      },
      {
        path: '/baz',
      }
    ]);
    deepEqual(result, ['/foo', '/foo/bar', '/baz']);
  });

  module('Ajax calls');

  test('addLocation', function() {
    deepEqual(wwwhisper.locations, []);
    var newLocation = {id: 13, path: '/foo', allowedUsers: []};
    mock_stub.expectAjaxCall('POST', 'api/locations/', {path: '/foo'},
                             newLocation);
    wwwhisper.addLocation('/foo');
    deepEqual(wwwhisper.locations, [newLocation]);
  });

  test('addLocation not invoked when location already exists', function() {
    deepEqual(wwwhisper.locations, []);
    // Only single ajax call is expected.
    mock_stub.expectAjaxCall('POST', 'api/locations/', {path: '/foo'},
                             { id: 13, path: '/foo', allowedUsers: []});
    wwwhisper.addLocation('/foo');
    wwwhisper.addLocation('/foo');
  });

  test('removeLocation', function() {
    wwwhisper.locations = [{
      id: 13,
      path: '/foo',
      self: 'example.com/locations/13',
      allowedUsers: [],
    }]
    mock_stub.expectAjaxCall('DELETE', wwwhisper.locations[0].self, null, null);
    wwwhisper.removeLocation(wwwhisper.locations[0]);
    deepEqual(wwwhisper.locations, []);
  });

  test('addUser', function() {
    var nextCallbackInvoked = false;
    deepEqual(wwwhisper.users, []);
    var newUser = {id: 13, email: 'foo@example.com'};
    mock_stub.expectAjaxCall('POST', 'api/users/', {email: 'foo@example.com'},
                             newUser);
    wwwhisper.addUser('foo@example.com',
                      function(userArg) {
                        nextCallbackInvoked = true;
                        deepEqual(userArg, newUser);
                      });
    ok(nextCallbackInvoked);
    deepEqual(wwwhisper.users, [newUser]);
  });

  test('removeUser', function() {
    wwwhisper.users = [{
      id: 13,
      email: 'foo@example.com',
      self: 'example.com/users/13',
    }]
    mock_stub.expectAjaxCall('DELETE', wwwhisper.users[0].self, null, null);
    wwwhisper.removeUser(wwwhisper.users[0]);
    deepEqual(wwwhisper.users, []);
  });

}());