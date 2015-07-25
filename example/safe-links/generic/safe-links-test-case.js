function SafeLinksTestCase(scenario) {
  this.scenario = scenario;
}

SafeLinksTestCase.prototype.start = function() {
  test(function() {

    var a = document.createElement("a");
    a.href = this.scenario.url;
    document.body.appendChild(a):

    a.addEventListener("imaginary-success-event", function() {
      assert_equals(this.scenario.expectation, "allowed",
                    "The request to the URL should be allowed.");
    });

    a.addEventListener("imaginary-error-event", function() {
      assert_equals(this.scenario.expectation, "blocked",
                    "The request to the URL should be blocked.");
    })

    a.click();

  }, this.scenario.description);
}

