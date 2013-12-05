import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import ndb
import data
import jinja2
import markdown2
import mcache
import re
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class AdminBase(webapp2.RequestHandler):
    def render(self, template_name, template_values):
        template = JINJA_ENVIRONMENT.get_template(template_name)
        return template.render(template_values)


class AdminPage(AdminBase):
    def get(self):
        user = users.get_current_user()
        config = data.Config.get_singleton()
        template_values = {
            'user': user,
            'config': config,
            }
        self.response.write(self.render('admin.html', template_values))

    def dispatch(self):
        user = users.get_current_user()
        config = data.Config.get_singleton()
        if config.is_author(user.email()):
            super(AdminPage, self).dispatch()
        else:
            self.abort(403)


class AdminConfigPage(AdminBase):
    def get(self):
        user = users.get_current_user()
        config = data.Config.get_singleton()
        template_values = {
            'user': user,
            'config': config,
            }
        self.response.write(self.render('config.html', template_values))


class AdminJsPage(AdminBase):
    def get(self):
        config = data.Config.get_singleton()
        self.response.write('$blogae_scripts = [];' + config.admin_script)


class AdminPickerPage(AdminBase):
    def get(self):
        user = users.get_current_user()
        config = data.Config.get_singleton()
        template_values = {
            'user': user,
            'config': config,
            }
        self.response.write(self.render('picker.html', template_values))


application = webapp2.WSGIApplication([
        ('/admin/config', AdminConfigPage),
        ('/admin/picker', AdminPickerPage),
        ('/admin/js', AdminJsPage),
        ('/admin', AdminPage),
    ], debug=True)
