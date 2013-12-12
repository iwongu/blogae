'use strict';


angular.module('blogae.topbar', []).factory('topbar', function() {
  return {
    show_message: function(msg) {
      var el = $('#topbar');
      el.text(msg);
      el.removeClass('hide');
      el.removeClass('error');
    },

    show_error: function(msg) {
      var el = $('#topbar');
      el.text(msg);
      el.removeClass('hide');
      el.addClass('error');
    },

    hide_message: function() {
      var el = $('#topbar');
      el.text('');
      el.addClass('hide');
    }
  };
});
