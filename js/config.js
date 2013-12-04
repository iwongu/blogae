'use strict';


// Declare app level module which depends on filters, and services
angular.module('myApp', [
    'ngRoute',
    'myApp.controllers',
]);

angular.module('myApp.controllers', []).controller('ConfigCtrl', [
    '$scope', '$http', '$element', '$window',
    function($scope, $http, $element, $window) {
	$scope.config = {};
	$scope.saving = true;

	$scope.save_config = function() {
	    $scope.saving = true;
	    var params = $.param($scope.config);
	    $http.defaults.headers.post["Content-Type"] = "application/x-www-form-urlencoded";
	    $http.post('/_/save_config/', params).success(function(data) {
		$scope.config = data.config;
		$scope.saving = false;
	    }).error(function() {
		// todo(iwongu): show error message.
	    });
	}

	$scope.fetch_config = function() {
	    $http.defaults.headers.post["Content-Type"] = "application/x-www-form-urlencoded";
	    $http.post('/_/get_config/').success(function(data) {
		$scope.config = data.config;
		$scope.saving = false;
	    }).error(function() {
		// todo(iwongu): show error message.
	    });
	}

	$scope.fetch_config();
    }]);
