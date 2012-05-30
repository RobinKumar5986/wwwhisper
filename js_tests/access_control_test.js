(function() {
  mock_stub = {
    expectedCalls: [],

    ajax: function(method, resource, params, successCallback) {
      if (this.expectedCalls.length === 0) {
        ok(false, 'Unexpected ajax call ' + method + ' ' + resource);
      }
    },

    expectAjaxCall: function(method, resource, params, result) {
    },
  };

  wwwhisper.stub = mock_stub;

  wwwhisper.ui = {
    refresh: function() {}
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

}());