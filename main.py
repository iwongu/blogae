import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

from google.appengine.api import users
from google.appengine.ext import ndb
import collections
import data
import datetime
import jinja2
import logging
import markdown2
import mcache
import re
import urllib
import webapp2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class MainBase(webapp2.RequestHandler):
    def render(self, template_name, template_values):
        template = JINJA_ENVIRONMENT.get_template(template_name)
        return template.render(template_values)

    def check_mcache(self, opt_key=''):
        response = mcache.get_path(self.request.path + opt_key)
        if response is not None:
            self.response.write(response)
            return True
        return False

    def set_mcache(self, response, opt_key=''):
        mcache.set_path(self.request.path + opt_key, response)

    def base_query(self):
        return data.Post.query(data.Post.is_draft == False)

    def handle_404(self):
        config = data.Config.get_singleton()
        template_values = {
            'config': config,
            'months': self.get_months(),
            }
        self.response.write(self.render('404.html', template_values))
        self.response.set_status(404)

    def get_months(self):
        """Builds months. It's extreamly slow since it's fetching all posts."""
        months =  mcache.get_months()
        if months is not None:
            return months

        posts = self.base_query().fetch()
        names = []
        for post in posts:
            names.append('%d/%02d' % (post.date_published.year, post.date_published.month))
        names.sort()

        current = names[0]
        months = {}
        months[current] = 0
        for name in names:
            if (name == current):
                months[name] += 1
            else:
                months[name] = 1
                current = name
        mcache.set_months(months)
        return months


class PageBase(MainBase):
    def handle_page(self, query, pagenum, pagelinkprefix, opt_template_values=None):
        if self.check_mcache():
            return

        config = data.Config.get_singleton()

        keys = query.fetch(keys_only=True)
        total_pagenum = (len(keys) / config.blog_page_size) + \
            (1 if len(keys) % config.blog_page_size != 0 else 0)

        startnum = config.blog_page_size * (pagenum - 1)
        fetchnum = startnum + config.blog_page_size + 1
        posts = query.fetch(fetchnum)
        has_next = len(posts) == fetchnum
        posts = posts[startnum:startnum + config.blog_page_size]
        if len(posts) == 0:
            self.handle_404()
            return
        for post in posts:
            post.add_converted_attributes(True)
        template_values = {
            'config': config,
            'posts': posts,
            'has_prev': pagenum > 1,
            'has_next': has_next,
            'page_num': pagenum,
            'total_page_num': total_pagenum,
            'page_link_prefix': pagelinkprefix,
            'months': self.get_months(),
        }
        if opt_template_values != None:
            template_values = dict(template_values.items() + opt_template_values.items())
        response = self.render('index.html', template_values)
        self.response.write(response)
        self.set_mcache(response)


class PagePage(PageBase):
    def get(self, opt_pagenumstr):
        pagenum = int(opt_pagenumstr) if opt_pagenumstr else 1
        self.handle_page(self.base_query().order(-data.Post.date_published), pagenum, "")


class MonthlyPage(PageBase):
    def get(self, yearstr, monthstr, opt_pagenumstr):
        pagenum = int(opt_pagenumstr) if opt_pagenumstr else 1
        startdate = datetime.datetime(int(yearstr), int(monthstr), 1)
        enddate = self.get_next_month(startdate)
        query = self.base_query().filter(
            data.Post.date_published >= startdate, data.Post.date_published < enddate) \
            .order(-data.Post.date_published)
        self.handle_page(query, pagenum, "/" + yearstr + "/" + monthstr,
                         {'selected_month':
                              '%d/%02d' % (int(yearstr), int(monthstr))})

    def get_next_month(self, date):
        if date.month == 12:
            return datetime.datetime(date.year + 1, 1, 1)
        else:
            return datetime.datetime(date.year, date.month + 1, 1)


class YearlyPage(PageBase):
    def get(self, yearstr, opt_pagenumstr):
        pagenum = int(opt_pagenumstr) if opt_pagenumstr else 1
        startdate = datetime.datetime(int(yearstr), 1, 1)
        enddate = datetime.datetime(int(yearstr) + 1, 1, 1)
        query = self.base_query().filter(
            data.Post.date_published >= startdate, data.Post.date_published < enddate) \
            .order(-data.Post.date_published)
        self.handle_page(query, pagenum, "/" + yearstr)


class TagPage(PageBase):
    def get(self, tag, opt_pagenumstr):
        tag = urllib.unquote_plus(tag)
        pagenum = int(opt_pagenumstr) if opt_pagenumstr else 1
        query = self.base_query().filter(data.Post.tags == tag).order(-data.Post.date_published)
        self.handle_page(query, pagenum, "/tag/" + urllib.quote_plus(tag))


class SearchPage(PageBase):
    def get(self, terms, opt_pagenumstr):
        terms = urllib.unquote_plus(terms)
        pagenum = int(opt_pagenumstr) if opt_pagenumstr else 1
        query = self.base_query()
        for term in re.split(r' +', terms):
            query = query.filter(data.Post.search_terms == term.lower())
        self.handle_page(query, pagenum, "/s/" + urllib.quote_plus(terms),
                         {'selected_search': urllib.quote_plus(terms)})


class PostBase(MainBase):
    def handle_post(self, post):
        if self.check_mcache():
            return

        config = data.Config.get_singleton()

        if post == None:
            self.handle_404()
            return
        prevquery = self.base_query().filter(data.Post.date_published > post.date_published) \
            .order(data.Post.date_published)
        prevpost = self.fetch_first(prevquery)
        
        nextquery = self.base_query().filter(data.Post.date_published < post.date_published) \
            .order(-data.Post.date_published)
        nextpost = self.fetch_first(nextquery)

        template_values = {
            'config': config,
            'post': post,
            'prev_post': prevpost,
            'next_post': nextpost,
        }
        response = self.render('post.html', template_values)
        self.response.write(response)
        self.set_mcache(response)

    def fetch_first(self, query):
        posts = query.fetch(1)
        return posts[0].add_converted_attributes() if len(posts) > 0 else None


class PermalinkPage(PostBase):
    def get(self, yearstr, monthstr, permalink):
        startdate = datetime.datetime(int(yearstr), int(monthstr), 1)
        postquery = self.base_query().filter(
            data.Post.date_published > startdate, data.Post.permalink == permalink) \
            .order(-data.Post.date_published)
        self.handle_post(self.fetch_first(postquery))


class FeedPage(MainBase):
    def get(self):
        sizestr = self.request.get('size', '10')
        size = int(sizestr)
        if size <= 0:
            self.abort(400)

        if self.check_mcache(sizestr):
            return

        config = data.Config.get_singleton()

        posts = self.base_query().order(-data.Post.date_published).fetch(size)
        for post in posts:
            post.add_converted_attributes(False, True)
        template_values = {
            'config': config,
            'posts': posts,
        }
        response = self.render('atom.xml', template_values)
        self.response.headers['Content-Type'] = 'application/xml'
        self.response.write(response)
        self.set_mcache(response, sizestr)



application = webapp2.WSGIApplication([
        ('/feed/', FeedPage),
        (r'/(?:page/(\d+))?', PagePage),
        (r'/(\d+)/(?:page/(\d+))?', YearlyPage),
        (r'/(\d+)/(\d+)/(?:page/(\d+))?', MonthlyPage),
        (r'/(\d+)/(\d+)/(.+)', PermalinkPage),
        (r'/tag/(.+)/(?:page/(\d+))?', TagPage),
        (r'/s/(.+)/(?:page/(\d+))?', SearchPage),
    ], debug=True)
