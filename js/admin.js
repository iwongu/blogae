'use strict';


// Declare app level module which depends on filters, and services
var adminApp = angular.module('blogae.admin', ['blogae.topbar', 'blogae.scroll']);

adminApp.controller('AdminCtrl', function($scope, $http, $window, topbar) {
  var admin = this;

  this.title = '';
  this.content = '';
  this.content_html = '';
  this.tags = '';
  this.permalink = '';
  this.date_published = '';

  this.posts = [];
  this.next_post_id = '';

  this.selected_post = null;
  this.edited = false;

  this.help_showing = false;

  this.saving = false;
  this.metadata_editing = 'tags'; // or published or permalink.
  this.blogae_scripts = $blogae_scripts;


  this.edit = function(postid) {
    angular.forEach(this.posts, angular.bind(this, function(post) {
      if (post.id == postid) {
        this.fill_post_form(post);
      }
    }));
  }

  // fills the post form. will lose the current post if any.
  this.fill_post_form = function(post) {
    if (this.has_changed() &&
	!$window.confirm('You will lose you data. Are you sure?')) {
      return;
    }

    this.selected_post = post;
    this.title = post.title;
    this.content = post.content;
    this.content_html = post.content_html;
    this.tags = post.tags;
    this.permalink = post.permalink;
    this.date_published = post.date_published;

    this.edited = false;
    this.content_changed();
  }

  this.has_changed = function() {
    var is_empty = !(this.title || this.content || this.selected_post);
    return !is_empty && this.edited;
  }

  this.view = function(postid) {
    angular.forEach(this.posts, angular.bind(this, function(post) {
      if (post.id == postid) {
	var permalink = post.permalink_full;
	$window.open(permalink, 'view');
      }
    }));
  }

  this.content_changed = function() {
    var html = markdown.toHTML(this.content);
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

  this.toggle_metadata_editing = function() {
    if (this.metadata_editing == 'tags') {
      this.metadata_editing = 'published';
    } else if (this.metadata_editing == 'published') {
      this.metadata_editing = 'permalink';
    } else {
      this.metadata_editing = 'tags';
    }
  }

  this.check_date_format = function() {
    var format = /\d{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4} \d{1,2}:\d{1,2}/;
    return this.date_published.length == 0 || format.test(this.date_published);
  }

  this.delete_post = function() {
    if (!$window.confirm('Are you sure you delete the post?')) {
      return;
    }

    var params = $.param({'postid': this.selected_post.id});
    topbar.show_message('deleting...');
    $http.post('/_/delete/', params).success(angular.bind(this, function(data) {
      var i = 0;
      for (; i < this.posts.length; i++) {
	if (this.posts[i].id == data.postid) {
	  break;
	}
      }
      this.posts.splice(i, 1);
      this.prepare_new_post();
      topbar.hide_message();
    })).error(angular.bind(this, function() {
      // todo(iwongu): show better error message.
      topbar.show_error('failed to delete...');
    }));
  }

  this.publish = function() {
    this.save_post('/_/publish/', false);
  }

  this.save = function() {
    this.save_post('/_/save/', true);
  }

  this.save_post = function(api_path, is_draft) {
    if (!this.check_date_format()) {
      $window.alert('The published date format is wrong.');
      return;
    }
    this.saving = true;
    var params = this.prepare_save();
    topbar.show_message('saving...');
    $http.post(api_path, params).success(angular.bind(this, function(post) {
      this.saving = false;
      this.edited = false;
      if (!this.selected_post) { // new post.
	this.selected_post = post;
	this.posts.unshift(post);
      } else {
	angular.forEach(this.posts, angular.bind(this, function(current, i) {
	  if (current.id == this.selected_post.id) {
	    this.posts[i] = post;
	  }
	}));
      }
      this.fill_post_form(post);
      topbar.hide_message();
    })).error(angular.bind(this, function() {
      this.saving = false;
      // todo(iwongu): show better error message.
      topbar.show_error('failed to save...');
    }));
  }

  this.new_post = function() {
    if (this.has_changed() &&
	!$window.confirm('You will lose you data. Are you sure?')) {
      return;
    }
    this.prepare_new_post();
  }

  this.prepare_new_post = function() {
    this.title = '';
    this.content = '';
    this.content_html = '';
    this.tags = '';
    this.permalink = '';
    this.date_published = '';

    this.selected_post = null;
    this.edited = false;
    this.content_changed();
  }

  this.prepare_save = function() {
    // save changes locally.
    if (this.selected_post) {
      this.selected_post.title = this.title;
      this.selected_post.content = this.content;
      this.selected_post.tags = this.tags;
      this.selected_post.permalink = this.permalink;
      this.selected_post.date_published = this.date_published;
    }

    return $.param({
      'postid': this.selected_post ? this.selected_post.id : '',
      'title': this.title,
      'content': this.content,
      'tags': this.tags,
      'permalink': this.selected_post ? this.selected_post.permalink : '',
      'date_published': this.selected_post ?
        this.selected_post.date_published : '',
    });
  }

  this.load_more = function() {
    if (this.next_post_id) {
      this.fetch_next(this.next_post_id);
    }
  };

  this.call_blogae_script = function(num) {
    this.content = this.blogae_scripts[num](this.content);
    this.edited = true;
    this.content_changed();
  }

  this.open_photo_picker = function() {
    createPicker(this.photos_selected.bind(this));
    /*
    var picker = $window.open('/admin/picker', 'picker');
    var timer = $window.setInterval(angular.bind(this, function() {
      if (picker.closed !== false) {
	$window.clearInterval(timer);
	this.photos_selected();
      }
    }), 200);
    */
  }

  this.photos_selected = function(data) {
    if (data[google.picker.Response.ACTION] == google.picker.Action.PICKED) {
      var docs = data[google.picker.Response.DOCUMENTS];

      var content_el = $('#content').get(0);
      var caret = content_el.selectionStart;
      var new_content = this.content.slice(0, caret);
      new_content += '\n';
      docs.map(function(doc) {
        var url = doc[google.picker.Document.THUMBNAILS][0]['url'].replace('/s32-c', '/s2048');
        new_content += '\n![](' + url + ')\n';
        new_content += '<img src="' + url + '" alt="" />\n';
        new_content += '<a href="' + url + '"><img src="' + url + '" alt="" /></a>\n';
      });

      new_content += '\n';
      new_content += this.content.slice(caret, this.content.length);
      this.content = new_content;
      this.edited = true;

      $scope.$apply();
      this.content_changed();
    }
  }
  /*
  this.photos_selected = function() {
    var value = $('#selected_photos').val();
    if (!value) {
      return;
    }
    var photos = value.split(' ');
    var content_el = $('#content').get(0);
    var caret = content_el.selectionStart;
    var new_content = this.content.slice(0, caret);
    new_content += '\n';
    for (var i = 0; i < photos.length; i++) {
      new_content += '\n![](' + photos[i] + ')\n';
    }
    new_content += '\n';
    new_content += this.content.slice(caret, this.content.length);
    this.content = new_content;
    this.edited = true;

    $scope.$apply();
    this.content_changed();
  }
  */

  this.fetch_next = function(next_post_id) {
    var params = $.param({'next_post_id': next_post_id});
    topbar.show_message('loading...');
    $http.post('/_/get_posts/', params).success(angular.bind(this, function(data) {
      this.posts = this.posts.concat(data.posts);
      this.next_post_id = data.next_post_id;
      topbar.hide_message();
    })).error(angular.bind(this, function() {
      // todo(iwongu): show beter error message.
      topbar.show_error('failed to fetch more posts...');
    }));
  }

  // set default header.
  $http.defaults.headers.post["Content-Type"] =
    "application/x-www-form-urlencoded";

  // fetch the posts when app is started.
  this.fetch_next('')
});
