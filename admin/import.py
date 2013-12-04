import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

from google.appengine.api import users
from google.appengine.ext import db
import data
import datetime
import html2text
import logging
import mcache
import re
import webapp2


class ImportPage(webapp2.RequestHandler):
    def post(self):
        post = data.Post()
        #post.author = user
        post.title = self.request.get('title')
        post.permalink = self.sanitizePermalink(post.title)
        post.content_html = self.request.get('content')
        post.content_html = re.sub(r'\n+', '<br>', post.content_html)
        post.content = html2text.html2text(post.content_html)
        post.date_published = datetime.datetime.fromtimestamp(
            int(self.request.get('date_published')))
        post.tags = self.request.get('tags').split(',')
        post.populate_terms()
        post.put()

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('')
        mcache.dirty_all()

    def sanitizePermalink(self, title):
        replaced = re.sub(r"\s+", "-", title)
        replaced = re.sub(r"[!@#$%^&*()`~_\\+=\\|\[\]{}<>,./?:;'\"]","", replaced)
        replaced = re.sub(r"-+", "-", replaced)
        return replaced.lower()


class PostImportPage(webapp2.RequestHandler):
    def get(self):
        # for post in data.Post.query().fetch():
        #     post.key.delete()
        
        user = users.get_current_user()
        for post in data.Post.query().fetch():
            if post.author == None:
                post.author = user
                post.put()

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('success')
        mcache.dirty_all()


application = webapp2.WSGIApplication([
        ('/import', ImportPage),
        ('/postimport', PostImportPage)
    ], debug=True)
