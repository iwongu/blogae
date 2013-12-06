import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

from google.appengine.api import users
from google.appengine.ext import ndb
import jinja2
import markdown2
import re


class Config(ndb.Model):
    blog_cover = ndb.StringProperty()
    blog_logo = ndb.StringProperty()
    blog_title = ndb.StringProperty()
    blog_url = ndb.StringProperty()
    blog_favicon = ndb.StringProperty()
    blog_page_size = ndb.IntegerProperty()
    blog_summary_size = ndb.IntegerProperty()
    authors = ndb.StringProperty(repeated=True)
    client_id = ndb.StringProperty()
    admin_script = ndb.TextProperty()
    blog_script = ndb.TextProperty()
    post_script = ndb.TextProperty()
    comment_script = ndb.TextProperty()

    @classmethod
    def get_singleton(cls):
        configs = cls.query().fetch()
        if len(configs) > 0:
            return configs[0]

        config_data = cls()
        config_data.blog_title = 'Your blog title'
        config_data.blog_page_size = 5
        config_data.blog_summary_size = 300
        config_data.put()
        return config_data;

    def is_author(self, user):
        return len(self.authors) == 0 or user in self.authors or users.is_current_user_admin()

    def serialize(self):
        return {
            'blog_cover': self.blog_cover,
            'blog_logo': self.blog_logo,
            'blog_title': self.blog_title,
            'blog_url': self.blog_url,
            'blog_favicon': self.blog_favicon,
            'blog_page_size': self.blog_page_size,
            'blog_summary_size': self.blog_summary_size,
            'authors': ','.join(self.authors),
            'client_id': self.client_id,
            'admin_script': self.admin_script,
            'blog_script': self.blog_script,
            'post_script': self.post_script,
            'comment_script': self.comment_script
            }


class Post(ndb.Model):
    author = ndb.UserProperty()
    title = ndb.StringProperty()
    content = ndb.TextProperty()  # markdown format.
    content_html = ndb.TextProperty()  # html format for imported posts.
    tags = ndb.StringProperty(repeated=True)
    permalink = ndb.StringProperty()
    is_draft = ndb.BooleanProperty(default=False)
    date_published = ndb.DateTimeProperty(auto_now_add=True)
    date_created = ndb.DateTimeProperty(auto_now_add=True)
    date_modified = ndb.DateTimeProperty(auto_now=True)
    search_terms = ndb.StringProperty(repeated=True)

    def serialize(self):
        return {
            'id': self.key.id(),
            'title': self.title,
            'content': self.content,
            'content_html': self.content_html,
            'tags': ','.join(self.tags),
            'permalink': self.permalink,
            'permalink_full': '/%d/%02d/%s' % (
                self.date_published.year, self.date_published.month, self.permalink),            
            'date_published': self.date_published.strftime('%d %b %Y %H:%M'),
            'date_published_epoch': self.date_published.strftime('%s'),
            'date_created': self.date_created.strftime('%d %b %Y %H:%M'),
            'date_created_epoch': self.date_created.strftime('%s'),
            'is_draft': self.is_draft
            }

    def add_converted_attributes(self, summary_only=False, for_atom=False):
        """
        Add converted attributes that templates will use.
        The extra attributes ends with "_converted".
        """
        config = Config.get_singleton()
        if summary_only:
            replaced = re.sub(r'\!\[.*?]\([^)]*\)', '', self.content)
            replaced = re.sub(r'[ \n]+', ' ', replaced)
            replaced = re.sub(r'[ \n]+', ' ', replaced)
            replaced = re.sub(r'<iframe.*?</iframe>', '', replaced)
            index = replaced.find(' ', config.blog_summary_size)
            summary = replaced[:index]
            if index != -1:
                summary += '...'
            self.content_converted = summary
        else:
            self.content_converted = jinja2.Markup(markdown2.markdown(self.content))

        if for_atom:
            tt = self.date_published.utctimetuple()
            self.date_published_converted = '%04d-%02d-%02dT%02d:%02d:%02dZ' % (
                tt.tm_year, tt.tm_mon, tt.tm_mday, tt.tm_hour, tt.tm_min, tt.tm_sec)
        else:
            self.date_published_converted = self.date_published.strftime('%d %b %Y')

        self.permalink_converted = '/%d/%02d/%s' % (
            self.date_published.year, self.date_published.month, self.permalink)
        first_photo_group = re.search(r'\!\[.*?]\(([^)]*)\)', self.content)
        if first_photo_group:
            self.main_photo_converted = first_photo_group.groups()[0]

        return self

    def populate_terms(self):
        delimiters = r'[ \n\'\".,*+/!?\[\]:~\-\(\)]+'
        title_terms = [
            term for term in re.split(delimiters, self.title) if len(term) > 0
            ]
        content_terms = [
            term for term in re.split(delimiters, self.content) if len(term) > 0
            ]
        date_terms = [
            str(self.date_published.year),
            str(self.date_published.month),
            str(self.date_published.day),
            ] if self.date_published else []
        terms = title_terms + content_terms + date_terms + self.tags + [self.permalink]
        terms = [term.lower() for term in terms]
        terms = list(set(terms))
        self.search_terms = [term.lower() for term in terms]
