'use strict';


// Declare app level module which depends on filters, and services
var admin = angular.module('blogae.admin', ['blogae.topbar', 'blogae.scroll']);

admin.controller('AdminCtrl', function($scope, $http, $window, topbar) {
  $scope.title = '';
  $scope.content = '';
  $scope.content_html = '';
  $scope.tags = '';
  $scope.permalink = '';
  $scope.date_published = '';

  $scope.posts = [];
  $scope.next_post_id = '';

  $scope.selected_post = null;
  $scope.edited = false;

  $scope.help_showing = false;

  $scope.saving = false;
  $scope.metadata_editing = 'tags'; // or published or permalink.
  $scope.blogae_scripts = $blogae_scripts;


  $scope.edit = function(postid) {
    angular.forEach($scope.posts, function(post) {
      if (post.id == postid) {
        $scope.fill_post_form(post);
      }
    });
  }

  // fills the post form. will lose the current post if any.
  $scope.fill_post_form = function(post) {
    if ($scope.has_changed() &&
	!$window.confirm('You will lose you data. Are you sure?')) {
      return;
    }

    $scope.selected_post = post;
    $scope.title = post.title;
    $scope.content = post.content;
    $scope.content_html = post.content_html;
    $scope.tags = post.tags;
    $scope.permalink = post.permalink;
    $scope.date_published = post.date_published;

    $scope.edited = false;
    $scope.content_changed();
  }

  $scope.has_changed = function() {
    var is_empty = !($scope.title || $scope.content || $scope.selected_post);
    return !is_empty && $scope.edited;
  }

  $scope.view = function(postid) {
    angular.forEach($scope.posts, function(post) {
      if (post.id == postid) {
	var permalink = post.permalink_full;
	$window.open(permalink, 'view');
      }
    });
  }

  $scope.content_changed = function() {
    var html = markdown.toHTML($scope.content);
    if (/iframe.*youtube.com.*\/iframe/.exec(html)) {
      // post-process to support youtube iframes.
      html = html.replace(/&lt;iframe /g, '<iframe ');
      html = html.replace(/&lt;\/iframe/g, '</iframe');
      html = html.replace(/&gt;/g, '>');
      html = html.replace(/&quot;/g, '"');
      html = html.replace(/<iframe width=".*?" height=".*?"/g,
                          '<iframe width="100%" height="auto"');
    }
    $('#post-preview').html(html);
  }

  $scope.toggle_metadata_editing = function() {
    if ($scope.metadata_editing == 'tags') {
      $scope.metadata_editing = 'published';
    } else if ($scope.metadata_editing == 'published') {
      $scope.metadata_editing = 'permalink';
    } else {
      $scope.metadata_editing = 'tags';
    }
  }

  $scope.check_date_format = function() {
    var format = /\d{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4} \d{1,2}:\d{1,2}/;
    return $scope.date_published.length == 0 || format.test($scope.date_published);
  }

  $scope.delete_post = function() {
    if (!$window.confirm('Are you sure you delete the post?')) {
      return;
    }

    var params = $.param({'postid': $scope.selected_post.id});
    topbar.show_message('deleting...');
    $http.post('/_/delete/', params).success(function(data) {
      var i = 0;
      for (; i < $scope.posts.length; i++) {
	if ($scope.posts[i].id == data.postid) {
	  break;
	}
      }
      $scope.posts.splice(i, 1);
      $scope.prepare_new_post();
      topbar.hide_message();
    }).error(function() {
      // todo(iwongu): show better error message.
      topbar.show_error('failed to delete...');
    });
  }

  $scope.publish = function() {
    $scope.save_post('/_/publish/', false);
  }

  $scope.save = function() {
    $scope.save_post('/_/save/', true);
  }

  $scope.save_post = function(api_path, is_draft) {
    if (!$scope.check_date_format()) {
      $window.alert('The published date format is wrong.');
      return;
    }
    $scope.saving = true;
    var params = $scope.prepare_save();
    topbar.show_message('saving...');
    $http.post(api_path, params).success(function(post) {
      $scope.saving = false;
      $scope.edited = false;
      if (!$scope.selected_post) { // new post.
	$scope.selected_post = post;
	$scope.posts.unshift(post);
      } else {
	angular.forEach($scope.posts, function(current, i) {
	  if (current.id == $scope.selected_post.id) {
	    $scope.posts[i] = post;
	  }
	});
      }
      $scope.fill_post_form(post);
      topbar.hide_message();
    }).error(function() {
      $scope.saving = false;
      // todo(iwongu): show better error message.
      topbar.show_error('failed to save...');
    });
  }

  $scope.new_post = function() {
    if ($scope.has_changed() &&
	!$window.confirm('You will lose you data. Are you sure?')) {
      return;
    }
    $scope.prepare_new_post();
  }

  $scope.prepare_new_post = function() {
    $scope.title = '';
    $scope.content = '';
    $scope.content_html = '';
    $scope.tags = '';
    $scope.permalink = '';
    $scope.date_published = '';

    $scope.selected_post = null;
    $scope.edited = false;
    $scope.content_changed();
  }

  $scope.prepare_save = function() {
    // save changes locally.
    if ($scope.selected_post) {
      $scope.selected_post.title = $scope.title;
      $scope.selected_post.content = $scope.content;
      $scope.selected_post.tags = $scope.tags;
      $scope.selected_post.permalink = $scope.permalink;
      $scope.selected_post.date_published = $scope.date_published;
    }

    return $.param({
      'postid': $scope.selected_post ? $scope.selected_post.id : '',
      'title': $scope.title,
      'content': $scope.content,
      'tags': $scope.tags,
      'permalink': $scope.selected_post ? $scope.selected_post.permalink : '',
      'date_published': $scope.selected_post ?
        $scope.selected_post.date_published : '',
    });
  }

  $scope.load_more = function() {
    if ($scope.next_post_id) {
      $scope.fetch_next($scope.next_post_id);
    }
  };

  $scope.call_blogae_script = function(num) {
    $scope.content = $scope.blogae_scripts[num]($scope.content);
    $scope.edited = true;
    $scope.content_changed();
  }

  $scope.open_photo_picker = function() {
    var picker = $window.open('/admin/picker', 'picker');
    var timer = $window.setInterval(function() {
      if (picker.closed !== false) {
	$window.clearInterval(timer);
	$scope.photos_selected();
      }
    }, 200);
  }

  $scope.photos_selected = function() {
    var value = $('#selected_photos').val();
    if (!value) {
      return;
    }
    var photos = value.split(' ');
    var content_el = $('#content').get(0);
    var caret = content_el.selectionStart;
    var new_content = $scope.content.slice(0, caret);
    new_content += '\n';
    for (var i = 0; i < photos.length; i++) {
      new_content += '\n![](' + photos[i] + ')\n';
    }
    new_content += '\n';
    new_content += $scope.content.slice(caret, $scope.content.length);
    $scope.content = new_content;
    $scope.edited = true;

    $scope.$apply();
    $scope.content_changed();
  }

  $scope.fetch_next = function(next_post_id) {
    var params = $.param({'next_post_id': next_post_id});
    topbar.show_message('loading...');
    $http.post('/_/get_posts/', params).success(function(data) {
      $scope.posts = $scope.posts.concat(data.posts);
      $scope.next_post_id = data.next_post_id;
      topbar.hide_message();
    }).error(function() {
      // todo(iwongu): show beter error message.
      topbar.show_error('failed to fetch more posts...');
    });
  }

  // set default header.
  $http.defaults.headers.post["Content-Type"] =
    "application/x-www-form-urlencoded";

  // fetch the posts when app is started.
  $scope.fetch_next('')
});
