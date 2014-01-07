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
    blog_custom_css = ndb.TextProperty()
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

        data = cls()
        data.blog_title = 'Your blog title'
        data.blog_page_size = 5
        data.blog_summary_size = 300
        data.put()
        return data;

    # todo(iwongu): change the method name to can_edit.
    def is_author(self, user):
        return len(self.authors) == 0 or user in self.authors or \
            users.is_current_user_admin()

    def serialize(self):
        return {
            'blog_cover': self.blog_cover,
            'blog_logo': self.blog_logo,
            'blog_title': self.blog_title,
            'blog_url': self.blog_url,
            'blog_favicon': self.blog_favicon,
            'blog_page_size': self.blog_page_size,
            'blog_summary_size': self.blog_summary_size,
            'blog_custom_css': self.blog_custom_css,
            'authors': ','.join(self.authors),
            'client_id': self.client_id,
            'admin_script': self.admin_script,
            'blog_script': self.blog_script,
            'post_script': self.post_script,
            'comment_script': self.comment_script
            }


class Author(ndb.Model):
    author = ndb.UserProperty()
    bio = ndb.TextProperty()

    @classmethod
    def get_author(cls, author):
        authors = cls.query(Author.author == author).fetch()
        if len(authors) > 0:
            return authors[0]

        data = cls()
        data.author = author
        data.put()
        return data

    def serialize(self):
        return {
            'author': {
                'email': self.author.email(),
                'nickname': self.author.nickname()
                },
            'bio': self.bio,
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
            'author': {
                'email': self.author.email(),
                'nickname': self.author.nickname()
                },
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
            'is_draft': self.is_draft,
            'editable': self.author == users.get_current_user() or users.is_current_user_admin()
            }

    def add_converted_attributes(self, summary_only=False, for_atom=False):
        """
        Add converted attributes that templates will use.
        The extra attributes ends with "_converted".
        """
        config = Config.get_singleton()
        if summary_only:
            replaced = re.sub(r'\!\[.*?]\([^)]*\)', '', self.content)
            replaced = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', replaced)
            replaced = re.sub(r'^#{1,6} ', '', replaced, flags=re.M)
            replaced = re.sub(r'^> ', '', replaced, flags=re.M)
            replaced = re.sub(r'\*\*(.+?)\*\*', r'\1', replaced, flags=re.M)
            replaced = re.sub(r'\*(.+?)\*', r'\1', replaced, flags=re.M)
            replaced = re.sub(r'^ *\* ', '', replaced, flags=re.M)
            replaced = re.sub(r'^ *\d\. ', '', replaced, flags=re.M)
            replaced = re.sub(r'[ \n]+', ' ', replaced, flags=re.M)
            replaced = re.sub(r'<iframe.*?</iframe>', '', replaced)
            index = replaced.find(' ', config.blog_summary_size)
            summary = replaced
            if index != -1:
                summary = replaced[:index]
                summary += '...'
            self.content_converted = summary
        else:
            self.content_converted = jinja2.Markup(markdown2.markdown(self.content))

        if for_atom:
            tt = self.date_published.utctimetuple()
            self.date_published_converted = '%04d-%02d-%02dT%02d:%02d:%02dZ' % (
                tt.tm_year, tt.tm_mon, tt.tm_mday, tt.tm_hour, tt.tm_min, tt.tm_sec)
        else:
            self.date_published_converted = self.date_published.strftime('%d %B %Y')

        self.permalink_converted = '/%d/%02d/%s' % (
            self.date_published.year, self.date_published.month, self.permalink)
        first_photo = re.search(r'\!\[.*?]\(([^)]*)\)', self.content)
        if first_photo:
            self.main_photo_converted = first_photo.groups()[0]
        else:
            first_youtube = re.search(r'src="//www.youtube.com/embed/(.*?)"', self.content)
            if first_youtube:
                self.main_photo_converted = \
                    '//img.youtube.com/vi/' + first_youtube.groups()[0] + '/0.jpg'

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
