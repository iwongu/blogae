from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api import users
import data
import datetime
import json
import logging
import mcache
import re
import urllib
import webapp2


class ApiBase(webapp2.RequestHandler):
    def get_post_author(self, post):
        user = users.get_current_user()
        if not (post.author == user or users.is_current_user_admin()):
            self.abort(403)
        return user

    def get_current_author(self):
        config = data.Config.get_singleton()
        user = users.get_current_user()
        if not (user in config.authors or users.is_current_user_admin()):
            self.abort(403)
        return user


class GetPosts(ApiBase):
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


class SavePost(ApiBase):
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
            self.get_post_author(post);
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


class DeletePost(ApiBase):
    def post(self):
        postid = self.request.get('postid')
        post = data.Post.get_by_id(int(postid))
        self.get_post_author(post);
        post.key.delete()
        self.response.write(json.dumps({'postid': postid}))
        mcache.dirty_all()


class GetConfig(ApiBase):
    def post(self):
        self.response.write(json.dumps({'config': data.Config.get_singleton().serialize()}))


class SaveConfig(ApiBase):
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
        config.blog_custom_css = self.request.get('blog_custom_css')
        config.authors = authors
        config.client_id = self.request.get('client_id')
        config.admin_script = self.request.get('admin_script')
        config.blog_script = self.request.get('blog_script')
        config.post_script = self.request.get('post_script')
        config.comment_script = self.request.get('comment_script')
        config.put()
        self.response.write(json.dumps({'config': config.serialize()}))
        mcache.dirty_all()


class GetAuthor(ApiBase):
    def post(self):
        user = self.get_current_author()
        author = data.Author.get_author(user);
        self.response.write(json.dumps({'author': author.serialize()}))


class SaveAuthor(ApiBase):
    def post(self):
        user = self.get_current_author()
        author = data.Author.get_author(user);
        author.bio = self.request.get('bio')
        author.put()
        self.response.write(json.dumps({'author': author.serialize()}))
        mcache.dirty_all()


class GetAlbums(ApiBase):
    def post(self):
        user = users.get_current_user()
        email = user.email()
        userid = email[0:email.find('@')]
        access_token = self.request.get('access_token')
        endpoint = 'https://picasaweb.google.com/data/feed/api/user/' + userid + \
            '?alt=json' + \
            '&access=all' + \
            '&start-index=' + self.request.get('start_index') + \
            '&max-results=' + self.request.get('max_results')
        headers = {'Authorization': 'Bearer ' + access_token}
        response = urlfetch.fetch(
            endpoint,
            method = urlfetch.GET,
            headers = headers)
        if response.status_code != 200:
            logging.error(str(response.status_code) + ': ' + response.content)
        self.response.write(json.dumps({
                    'status_code': response.status_code,
                    'content': response.content
                    }))


class GetPhotos(ApiBase):
    def post(self):
        user = users.get_current_user()
        access_token = self.request.get('access_token')
        endpoint = self.request.get('album_id') + \
            '&access=all&imgmax=1600' + \
            '&start-index=' + self.request.get('start_index') + \
            '&max-results=' + self.request.get('max_results')
        headers = {'Authorization': 'Bearer ' + access_token}
        response = urlfetch.fetch(
            endpoint,
            method = urlfetch.GET,
            headers = headers)
        self.response.write(json.dumps({
                    'status_code': response.status_code,
                    'content': response.content
                    }))


application = webapp2.WSGIApplication([
        ('/_/get_posts/', GetPosts),
        ('/_/publish/', PublishPost),
        ('/_/save/', SavePost),
        ('/_/delete/', DeletePost),
        ('/_/get_config/', GetConfig),
        ('/_/save_config/', SaveConfig),
        ('/_/get_author/', GetAuthor),
        ('/_/save_author/', SaveAuthor),
        ('/_/get_albums/', GetAlbums),
        ('/_/get_photos/', GetPhotos),
    ], debug=True)
