'use strict';


angular.module('blogae.scroll', []).directive('whenScrolled', function() {
  return function(scope, elem, attrs) {
    var raw = elem[0];
    elem.bind('scroll', function() {
      if (raw.scrollTop + raw.offsetHeight >= raw.scrollHeight) {
        scope.$apply(attrs.whenScrolled);
      }
    });
  };
});
