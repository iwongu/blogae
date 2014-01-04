'use strict';


angular.module('blogae.picker', [
  'blogae.picker.controllers',
  'blogae.scroll',
  'blogae.topbar',
]);

angular.module('blogae.picker.controllers', ['blogae.topbar']).
  controller('PickerCtrl', ['$scope', '$http', '$window', 'topbar',

  function($scope, $http, $window, topbar) {
    $scope.config = null;
    $scope.access_token = '';

    $scope.album_start_index = 1; // 1-based.
    $scope.album_max_results = 50;
    $scope.albums = [];
    $scope.current_album_id = '';

    $scope.photo_start_index = 1; // 1-based.
    $scope.photo_max_results = 200;
    $scope.photos = [];

    $scope.selected_photos = [];
    $scope.selected_photo_ids = [];

    $scope.is_zooming = false;
    $scope.zoomed_photo = null;

    $scope.cancel = function() {
      $window.opener.document.getElementById('selected_photos').value = '';
      $window.close();
    }

    $scope.done = function() {
      var photos = '';
      for (var i = 0; i < $scope.selected_photos.length; i++) {
        var photo = $scope.selected_photos[i];
        photos += ' ' + encodeURI(photo.src)
      }
      $window.opener.document.getElementById('selected_photos').value =
        photos.substring(1, photos.length);
      $window.close();
    }

    $scope.zoom_photo = function(photo) {
      $scope.zoomed_photo = photo;
      $scope.is_zooming = true;
    }

    $scope.stop_zoom = function() {
      $scope.is_zooming = false;
    }

    $scope.select_photo = function(photo) {
      if ($scope.selected_photo_ids.indexOf(photo.photo_id) == -1) {
        $scope.selected_photo_ids.push(photo.photo_id);
        $scope.selected_photos.push(photo);
        photo.selected = true;
      }
    }

    $scope.deselect_photo = function(photo) {
      var index = $scope.selected_photo_ids.indexOf(photo.photo_id);
      if (index != -1) {
        $scope.selected_photo_ids.splice(index, 1);
        $scope.selected_photos.splice(index, 1);
        photo.selected = false;
      }
    }

    $scope.load_more_photos = function() {
      if ($scope.photos.length + 1 == $scope.photo_start_index) {
        $scope.fetch_photos();
      }
    }

    $scope.fill_photos = function(data) {
      $scope.photo_start_index += $scope.photo_max_results;
      for (var i = 0; i < data.feed.entry.length; i++) {
        var entry = data.feed.entry[i];
        $scope.photos.push({
          'photo_id': entry.id.$t,
          'src': entry.content.src,
          'thumbnail_small': entry.media$group.media$thumbnail[0].url,
          'thumbnail_medium': entry.media$group.media$thumbnail[1].url,
          'thumbnail_large': entry.media$group.media$thumbnail[2].url,
          'selected': $scope.selected_photo_ids.indexOf(entry.id.$t) != -1
        })
      }
    }

    $scope.show_album_photos = function(album_id) {
      $scope.photo_start_index = 1;
      $scope.photos = [];

      $scope.current_album_id = album_id;
      $scope.fetch_photos();
    }

    $scope.photo_cache = {};

    $scope.fetch_photos = function() {
      var params = $.param({
        'access_token': $scope.access_token,
        'start_index': $scope.photo_start_index,
        'max_results': $scope.photo_max_results,
        'album_id': $scope.current_album_id
      });

      // check cache.
      if (params in $scope.photo_cache) {
        $scope.fill_photos(angular.fromJson($scope.photo_cache[params]));
        return;
      }

      topbar.show_message('loading...');
      $http.post('/_/get_photos/', params).success(function(response) {
        if (response.status_code == '200') {
          $scope.photo_cache[params] = response.content;
          $scope.fill_photos(angular.fromJson(response.content))
          topbar.hide_message();
        } else {
          // todo(iwongu): show better error message.
          topbar.show_error('failed to load... ' + response.content);
        }
      }).error(function() {
        // todo(iwongu): show better error message.
        topbar.show_error('failed to load...');
      });
    }

    $scope.load_more_albums = function() {
      if ($scope.albums.length + 1 == $scope.album_start_index) {
        $scope.fetch_albums();
      }
    }

    $scope.fill_albums = function(data) {
      $scope.album_start_index += $scope.album_max_results;
      for (var i = 0; i < data.feed.entry.length; i++) {
        var entry = data.feed.entry[i];
        var is_from_post =
          (entry.gphoto$albumType && entry.gphoto$albumType.$t) == 'Buzz'
        $scope.albums.push({
          'title': entry.title.$t,
          'thumbnail': entry.media$group.media$thumbnail[0].url,
          'album_id': entry.link[0].href,
          'num_photos': entry.gphoto$numphotos.$t,
          'is_from_post': is_from_post
        })
      }
    }

    $scope.fetch_albums = function() {
      var params = $.param({
        'access_token': $scope.access_token,
        'start_index': $scope.album_start_index,
        'max_results': $scope.album_max_results
      });

      topbar.show_message('loading...');
      $http.post('/_/get_albums/', params).success(function(response) {
        if (response.status_code == '200') {
          $scope.fill_albums(angular.fromJson(response.content))
          topbar.hide_message();
        } else {
          // todo(iwongu): show better error message.
          topbar.show_error('failed to load... ' + response.content);
        }
      }).error(function() {
        // todo(iwongu): show better error message.
        topbar.show_error('failed to load...');
      });
    }


    $scope.check_oauth2 = function() {
      if (window.location.hash) {
        $scope.access_token =
          $window.location.hash.match(/#access_token=(.*?)&.*/)[1];
        $scope.fetch_albums();
        return;
      }

      var endpoint = 'https://accounts.google.com/o/oauth2/auth';
      var params = {
        'response_type': 'token',
        'client_id': $scope.config.client_id,
        'redirect_uri': $window.location.href,
        'scope': 'https://picasaweb.google.com/data/'
      };

      var url_params = [];
      for (var name in params) {
        url_params.push(
          encodeURIComponent(name) + '=' + encodeURIComponent(params[name]));
      }
      window.location = endpoint + '?' + url_params.join("&");
    }

    $scope.fetch_config = function() {
      $http.post('/_/get_config/').success(function(data) {
        $scope.config = data.config;
        $scope.check_oauth2();
      }).error(function() {
        // todo(iwongu): show error message.
      });
    }

    $http.defaults.headers.post["Content-Type"] =
      "application/x-www-form-urlencoded";

    $scope.fetch_config();
  }]);
