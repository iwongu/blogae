'use strict';


angular.module('blogae.config', [
    'blogae.config.controllers'
]);

angular.module('blogae.config.controllers', []).controller('ConfigCtrl', [
    '$scope', '$http',
    function($scope, $http) {
	$scope.config = {};
	$scope.saving = true;

	$scope.save_config = function() {
	    $scope.saving = true;
	    var params = $.param($scope.config);
	    $http.post('/_/save_config/', params).success(function(data) {
		$scope.config = data.config;
		$scope.saving = false;
	    }).error(function() {
		// todo(iwongu): show error message.
	    });
	}

	$scope.fetch_config = function() {
	    $http.post('/_/get_config/').success(function(data) {
		$scope.config = data.config;
		$scope.saving = false;
	    }).error(function() {
		// todo(iwongu): show error message.
	    });
	}

	$http.defaults.headers.post["Content-Type"] =
            "application/x-www-form-urlencoded";
	$scope.fetch_config();
    }]);
