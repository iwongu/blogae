'use strict';


// Declare app level module which depends on filters, and services
var adminApp = angular.module('blogae.admin', ['blogae.topbar', 'blogae.scroll']);

adminApp.controller('AdminCtrl', function($scope, $http, $window, topbar) {
  var admin = this;

  admin.title = '';
  admin.content = '';
  admin.content_html = '';
  admin.tags = '';
  admin.permalink = '';
  admin.date_published = '';

  admin.posts = [];
  admin.next_post_id = '';

  admin.selected_post = null;
  admin.edited = false;

  admin.help_showing = false;

  admin.saving = false;
  admin.metadata_editing = 'tags'; // or published or permalink.
  admin.blogae_scripts = $blogae_scripts;


  admin.edit = function(postid) {
    angular.forEach(admin.posts, function(post) {
      if (post.id == postid) {
        admin.fill_post_form(post);
      }
    });
  }

  // fills the post form. will lose the current post if any.
  admin.fill_post_form = function(post) {
    if (admin.has_changed() &&
	!$window.confirm('You will lose you data. Are you sure?')) {
      return;
    }

    admin.selected_post = post;
    admin.title = post.title;
    admin.content = post.content;
    admin.content_html = post.content_html;
    admin.tags = post.tags;
    admin.permalink = post.permalink;
    admin.date_published = post.date_published;

    admin.edited = false;
    admin.content_changed();
  }

  admin.has_changed = function() {
    var is_empty = !(admin.title || admin.content || admin.selected_post);
    return !is_empty && admin.edited;
  }

  admin.view = function(postid) {
    angular.forEach(admin.posts, function(post) {
      if (post.id == postid) {
	var permalink = post.permalink_full;
	$window.open(permalink, 'view');
      }
    });
  }

  admin.content_changed = function() {
    var html = markdown.toHTML(admin.content);
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

  admin.toggle_metadata_editing = function() {
    if (admin.metadata_editing == 'tags') {
      admin.metadata_editing = 'published';
    } else if (admin.metadata_editing == 'published') {
      admin.metadata_editing = 'permalink';
    } else {
      admin.metadata_editing = 'tags';
    }
  }

  admin.check_date_format = function() {
    var format = /\d{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4} \d{1,2}:\d{1,2}/;
    return admin.date_published.length == 0 || format.test(admin.date_published);
  }

  admin.delete_post = function() {
    if (!$window.confirm('Are you sure you delete the post?')) {
      return;
    }

    var params = $.param({'postid': admin.selected_post.id});
    topbar.show_message('deleting...');
    $http.post('/_/delete/', params).success(function(data) {
      var i = 0;
      for (; i < admin.posts.length; i++) {
	if (admin.posts[i].id == data.postid) {
	  break;
	}
      }
      admin.posts.splice(i, 1);
      admin.prepare_new_post();
      topbar.hide_message();
    }).error(function() {
      // todo(iwongu): show better error message.
      topbar.show_error('failed to delete...');
    });
  }

  admin.publish = function() {
    admin.save_post('/_/publish/', false);
  }

  admin.save = function() {
    admin.save_post('/_/save/', true);
  }

  admin.save_post = function(api_path, is_draft) {
    if (!admin.check_date_format()) {
      $window.alert('The published date format is wrong.');
      return;
    }
    admin.saving = true;
    var params = admin.prepare_save();
    topbar.show_message('saving...');
    $http.post(api_path, params).success(function(post) {
      admin.saving = false;
      admin.edited = false;
      if (!admin.selected_post) { // new post.
	admin.selected_post = post;
	admin.posts.unshift(post);
      } else {
	angular.forEach(admin.posts, function(current, i) {
	  if (current.id == admin.selected_post.id) {
	    admin.posts[i] = post;
	  }
	});
      }
      admin.fill_post_form(post);
      topbar.hide_message();
    }).error(function() {
      admin.saving = false;
      // todo(iwongu): show better error message.
      topbar.show_error('failed to save...');
    });
  }

  admin.new_post = function() {
    if (admin.has_changed() &&
	!$window.confirm('You will lose you data. Are you sure?')) {
      return;
    }
    admin.prepare_new_post();
  }

  admin.prepare_new_post = function() {
    admin.title = '';
    admin.content = '';
    admin.content_html = '';
    admin.tags = '';
    admin.permalink = '';
    admin.date_published = '';

    admin.selected_post = null;
    admin.edited = false;
    admin.content_changed();
  }

  admin.prepare_save = function() {
    // save changes locally.
    if (admin.selected_post) {
      admin.selected_post.title = admin.title;
      admin.selected_post.content = admin.content;
      admin.selected_post.tags = admin.tags;
      admin.selected_post.permalink = admin.permalink;
      admin.selected_post.date_published = admin.date_published;
    }

    return $.param({
      'postid': admin.selected_post ? admin.selected_post.id : '',
      'title': admin.title,
      'content': admin.content,
      'tags': admin.tags,
      'permalink': admin.selected_post ? admin.selected_post.permalink : '',
      'date_published': admin.selected_post ?
        admin.selected_post.date_published : '',
    });
  }

  admin.load_more = function() {
    if (admin.next_post_id) {
      admin.fetch_next(admin.next_post_id);
    }
  };

  admin.call_blogae_script = function(num) {
    admin.content = admin.blogae_scripts[num](admin.content);
    admin.edited = true;
    admin.content_changed();
  }

  admin.open_photo_picker = function() {
    var picker = $window.open('/admin/picker', 'picker');
    var timer = $window.setInterval(function() {
      if (picker.closed !== false) {
	$window.clearInterval(timer);
	admin.photos_selected();
      }
    }, 200);
  }

  admin.photos_selected = function() {
    var value = $('#selected_photos').val();
    if (!value) {
      return;
    }
    var photos = value.split(' ');
    var content_el = $('#content').get(0);
    var caret = content_el.selectionStart;
    var new_content = admin.content.slice(0, caret);
    new_content += '\n';
    for (var i = 0; i < photos.length; i++) {
      new_content += '\n![](' + photos[i] + ')\n';
    }
    new_content += '\n';
    new_content += admin.content.slice(caret, admin.content.length);
    admin.content = new_content;
    admin.edited = true;

    admin.$apply();
    admin.content_changed();
  }

  admin.fetch_next = function(next_post_id) {
    var params = $.param({'next_post_id': next_post_id});
    topbar.show_message('loading...');
    $http.post('/_/get_posts/', params).success(function(data) {
      admin.posts = admin.posts.concat(data.posts);
      admin.next_post_id = data.next_post_id;
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
  admin.fetch_next('')
});
