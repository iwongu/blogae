from google.appengine.api import memcache
from google.appengine.api import users
import data
import datetime
import json
import logging
import mcache
import re
import urllib
import webapp2


class GetPosts(webapp2.RequestHandler):
    """Gets posts. If next_post_id is given, this will fetch from the id."""
    def post(self):
        config = data.Config.get_singleton()
        fetch_num = 30
        next_post_id = self.request.get('next_post_id')
        if len(next_post_id) == 0:
            query = data.Post.query()
        else:
            post = data.Post.get_by_id(int(next_post_id))
            query = data.Post.query(data.Post.date_published <= post.date_published)

        posts = query.order(-data.Post.date_published).fetch(fetch_num + 1)
        has_next = len(posts) == fetch_num + 1
        next_post_id = posts[-1].key.id() if has_next else ''
        posts = posts[0:-1] if has_next else posts

        response = {
            'posts': [post.serialize() for post in posts],
            'next_post_id': next_post_id
            }

        self.response.write(json.dumps(response))


class SavePost(webapp2.RequestHandler):
    def post(self):
        self.save_post(True)

    def save_post(self, is_draft):
        user = users.get_current_user()

        postid = self.request.get('postid')
        title = self.request.get('title')
        content = self.request.get('content')
        tags = self.request.get('tags')
        permalink = self.request.get('permalink')
        date_published = self.request.get('date_published')

        if len(postid) == 0:
            post = data.Post()
            post.author = user
            post.permalink = self.sanitize_permalink(title)
        else:
            post = data.Post.get_by_id(int(postid))
            if len(permalink) > 0:
                post.permalink = self.sanitize_permalink(permalink)
            else:
                post.permalink = self.sanitize_permalink(title)

            if len(date_published) > 0:
                post.date_published = datetime.datetime.strptime(date_published, '%d %b %Y %H:%M')
            else:
                post.date_published = datetime.now()

        post.title = title
        post.content = content
        post.is_draft = is_draft
        post.tags = self.sanitize_tags(tags)
        post.populate_terms()
        post.put()

        self.response.write(json.dumps(post.serialize()))
        mcache.dirty_all()

    def sanitize_tags(self, tags):
        sanitized = [self.sanitize_tag(tag) for tag in tags.split(',')]
        sanitized = [tag for tag in sanitized if tag]
        return list(set(sanitized))

    def sanitize_tag(self, tag):
        replaced = re.sub(r"\s+", " ", tag)
        return replaced.strip()

    def sanitize_permalink(self, title):
        replaced = re.sub(r"\s+", "-", title)
        replaced = re.sub(r"[!@#$%^&*()`~_\\+=\\|\[\]{}<>,./?:;'\"]","", replaced)
        replaced = re.sub(r"-+", "-", replaced)
        return replaced.lower()


class PublishPost(SavePost):
    def post(self):
        self.save_post(False)


class DeletePost(webapp2.RequestHandler):
    def post(self):
        postid = self.request.get('postid')
        post = data.Post.get_by_id(int(postid))
        post.key.delete()
        self.response.write(json.dumps({'postid': postid}))
        mcache.dirty_all()


class GetConfig(webapp2.RequestHandler):
    def post(self):
        self.response.write(json.dumps({'config': data.Config.get_singleton().serialize()}))


class SaveConfig(webapp2.RequestHandler):
    def post(self):
        authors = [
            author.strip()
            for author in self.request.get('authors').split(',')
            if len(author.strip()) > 0
            ]

        config = data.Config.get_singleton()
        config.blog_cover = self.request.get('blog_cover')
        config.blog_logo = self.request.get('blog_logo')
        config.blog_title = self.request.get('blog_title')
        config.blog_url = self.request.get('blog_url')
        config.blog_favicon = self.request.get('blog_favicon')
        config.blog_page_size = int(self.request.get('blog_page_size'))
        config.blog_summary_size = int(self.request.get('blog_summary_size'))
        config.authors = authors
        config.admin_script = self.request.get('admin_script')
        config.blog_script = self.request.get('blog_script')
        config.post_script = self.request.get('post_script')
        config.comment_script = self.request.get('comment_script')
        config.put()
        self.response.write(json.dumps({'config': config.serialize()}))
        mcache.dirty_all()


application = webapp2.WSGIApplication([
        ('/_/get_posts/', GetPosts),
        ('/_/publish/', PublishPost),
        ('/_/save/', SavePost),
        ('/_/delete/', DeletePost),
        ('/_/get_config/', GetConfig),
        ('/_/save_config/', SaveConfig),
    ], debug=True)
