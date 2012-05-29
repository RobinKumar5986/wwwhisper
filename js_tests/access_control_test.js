(function() {
  module("Utility functions");

  wwwhisper.stub = {
    ajax: function(method, resource, params, successCallback) {
      //ok(false, "Unexpected ajax call.");
      successCallback();
    }
  };

  wwwhisper.ui = {
    refresh: function() {
    }
  };

  test("inArray", function() {
    ok(wwwhisper.inArray(2, [1, 2, 3]));
    ok(wwwhisper.inArray("a", ["a", "b", "c"]));
    ok(wwwhisper.inArray("foo", ["bar", "baz", "foo"]));
    ok(wwwhisper.inArray("foo", ["foo", "foo", "foo"]));
    ok(wwwhisper.inArray(true, [true]));

    ok(!wwwhisper.inArray("foo", []));
    ok(!wwwhisper.inArray("foo", ["fooz"]));
    ok(!wwwhisper.inArray(1, [[1], 2, 3]));
  });

  test("removeFromArray", function() {
    var array = new Array("aa", "bb", "cc");
    wwwhisper.removeFromArray("bb", array);
    deepEqual(array, ["aa", "cc"]);
    wwwhisper.removeFromArray("cc", array);
    deepEqual(array, ["aa"]);
    wwwhisper.removeFromArray("a", array);
    deepEqual(array, ["aa"]);
    wwwhisper.removeFromArray("aa", array);
    deepEqual(array, []);
    wwwhisper.removeFromArray(null, array);
    deepEqual(array, []);
  });

  test("", function() {
    $.ajax = function(arg) {
      alert('called');
    };
    wwwhisper.addUser('wee@wp.pl', function() {alert('called')});
    ok(true);
  });
}());