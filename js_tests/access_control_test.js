(function () {
  test("inArrayTest", function() {
    ok(wwwhisper.inArray(2, [1, 2, 3]));
    ok(wwwhisper.inArray("a", ["a", "b", "c"]));
    ok(wwwhisper.inArray("foo", ["bar", "baz", "foo"]));
    ok(wwwhisper.inArray("foo", ["foo", "foo", "foo"]));
    ok(wwwhisper.inArray(true, [true]));

    ok(!wwwhisper.inArray("foo", []));
    ok(!wwwhisper.inArray("foo", ["fooz"]));
    ok(!wwwhisper.inArray(1, [[1], 2, 3]));
  });
}());