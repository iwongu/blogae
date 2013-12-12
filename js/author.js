'use strict';


angular.module('blogae.author', [
  'blogae.author.controllers'
]);

angular.module('blogae.author.controllers', []).
  controller('AuthorCtrl', ['$scope', '$http',
  function($scope, $http) {
    $scope.author = {};
    $scope.saving = true;

    $scope.save_config = function() {
      $scope.saving = true;
      var params = $.param($scope.author);
      $http.post('/_/save_author/', params).success(function(data) {
	$scope.author = data.author;
	$scope.saving = false;
      }).error(function() {
	// todo(iwongu): show error message.
      });
    }

    $scope.fetch_config = function() {
      $http.post('/_/get_author/').success(function(data) {
	$scope.author = data.author;
	$scope.saving = false;
      }).error(function() {
	// todo(iwongu): show error message.
      });
    }

    $http.defaults.headers.post["Content-Type"] =
      "application/x-www-form-urlencoded";
    $scope.fetch_config();
  }]);
