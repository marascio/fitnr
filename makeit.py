#!/usr/bin/env python
#
# $Id: makeit.py 245 2008-07-15 02:20:29Z louis $

import os, sys, re, shutil
import os.path as path
import dateutil.parser as dateutil

from markdown import Markdown, markdown
from smartypants import smartyPants
from jinja2 import Environment, FileSystemLoader, Template

BUILD_DIR        = 'build'
ARCHIVE_DIR      = 'archives'
CONTENT_DIR      = 'content'

# the base URL of the website
BASE_URL         = 'http://www.fitnr.com'

# the archive relative URL: /archives/<year>/<month>/<guid>.html
ARCHIVE_URL_FMT  = '/' + ARCHIVE_DIR + '/%s/%s/%s'

# name of the template to use for rending individual archive posts.
ARCHIVE_TEMPLATE = 'archivepost.html'

# when did I fix the GUIDs
GUID_FIX_DATE    = dateutil.parse('July 12, 2008 00:00:00 -0500')

header_whitespace_re = re.compile(r'^\s+\w')

class Post:
    headers = {}

    def compare(a, b):
        a_rev = dateutil.parse(a.revised)
        b_rev = dateutil.parse(b.revised)
        ret = cmp(a_rev, b_rev)
        
        if not ret:
            a_pub = dateutil.parse(a.published)
            b_pub = dateutil.parse(b.published)
            ret = cmp(a_pub, b_pub)

        return ret

    def __init__(self, filename):
        self.filename = filename
        self.raw_data = open(filename).read()

        header, self.body = map(lambda x: x.strip(),
                                self.raw_data.split('\n\n', 1))
        raw_hdrs = header.split('\n')
        self.process_headers(raw_hdrs)
        self.calculate_guid()

        self.url          = self.get_url()
        self.relative_url = self.get_relative_url()

    def __getitem__(self, item):
        return self.__dict__[item]

    def should_use_old_guid_fmt(self):
        if self.published:
            pub = dateutil.parse(self.published)
            return pub < GUID_FIX_DATE 
        return False

    def calculate_guid(self):
        # Ensure we clean up the filename, could be really dirty like
        # this: '/a/b/c/d/this-is-the-guid.post/'. This should become
        # 'this-is-the-guid'
        self.guid = re.sub('^/*(\w+/)*|.post(/*)$', '', self.filename)

    def process_headers(self, raw_hdrs):
        for h in raw_hdrs:
            if header_whitespace_re.match(h):
                self.__dict__[name] += ' ' + h.strip()
            else:
                name, value = map(lambda x: x.strip(), h.split(':', 1))
                self.headers[name] = value
                if self.__dict__.has_key(name) == False:
                    self.__dict__[name] = value

    def get_archive_dir(self):
        return path.join(ARCHIVE_DIR, self.get_year(),self.get_month())

    def get_archive_file(self):
        return self.guid + '.html'

    def get_relative_url(self):
        return ARCHIVE_URL_FMT % (self.get_year(), self.get_month(),
                                  self.get_archive_file())

    def get_guid(self):
        if self.should_use_old_guid_fmt():
            return BASE_URL + '/' + self.get_relative_url()
        else:
            return BASE_URL + self.get_relative_url()

    def get_url(self):
        return BASE_URL + self.get_relative_url()
    
    def get_year(self):
        d = dateutil.parse(self.published)
        return "%04d" % d.year

    def get_month(self):
        d = dateutil.parse(self.published)
        return "%02d" % d.month

    def get_tags(self):
        new_tags = []
        tags = self.tags.split(',')
        for t in tags:
            t = t.strip().replace(' ', '-')
            new_tags.append(t)
        return new_tags

def do_markdown(content):
    md = Markdown(extensions=['footnotes'])
    return smartyPants(md.convert(content))

def do_rfc2822_datetime(content):
    d = dateutil.parse(content)
    return d.strftime("%a, %d %b %Y %H:%M:%S %z")

def do_friendly_datetime(content):
    d = dateutil.parse(content)
    return d.strftime("%B %d, %Y")

def do_isoformat_datetime(content):
    d = dateutil.parse(content)
    return d.isoformat()

# published and embargo are defined in the main block, is this correct?
def do_internal_links(content, published, relative):
    for post in published:
        i = re.finditer(r'\$[\w-]*', content)
        for s in i:
            link = content[s.start():s.end()]
            dest_post = find_post_with_guid(link[1:], published);
            if dest_post is not None:
                new_data  = content[0:s.start()]
                if relative: new_data += dest_post.get_relative_url()
                else       : new_data += dest_post.get_url()
                new_data += content[s.end():]
                content   = new_data
    return content

def make_build_dest_dir(dir):
    dest_dir = path.join(BUILD_DIR, dir)
    if not path.exists(dest_dir):
        os.makedirs(dest_dir)
    return dest_dir

def find_post_with_guid(guid, posts):
    for post in posts:
        if post.guid == guid:
            return post

    return None

if __name__ == '__main__':
    pages_files = []
    published = []
    embargo = []

    # Find all of the content sources
    for root, dirs, files in os.walk(CONTENT_DIR):
        if len(files) > 0:
            for f in files:
                if f.endswith('post'):
                    file = path.join(root, f) 
                    post = Post(file)
                    if post.published:
                        published.append(post)
                    else:
                        embargo.append(post)

    published.sort(Post.compare)
    published.reverse()

    embargo.sort(Post.compare)
    embargo.reverse()

    env = Environment(loader=FileSystemLoader(['.', 'templates']))

    env.filters['markdown']           = do_markdown
    env.filters['rfc2822_datetime']   = do_rfc2822_datetime
    env.filters['friendly_datetime']  = do_friendly_datetime
    env.filters['isoformat_datetime'] = do_isoformat_datetime
    env.filters['internal_links']     = do_internal_links

    if path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)

    shutil.copytree('assets', BUILD_DIR)

    for root, dirs, files in os.walk('pages'):
        if len(files) > 0:
            for f in files:
                if f.endswith('html') or f.endswith('xml'):
                    file = path.join(root, f) 
                    pages_files.append(file)

    for file in pages_files:
        t = env.get_template(file)
        page = t.render(published=published, embargo=embargo)

        dest_dir = make_build_dest_dir(path.dirname(file.split(os.sep, 1)[1]))

        f = open(path.join(dest_dir, path.basename(file)), 'w')
        f.write(page)
        f.close()

    for post in published:
        t = env.get_template(ARCHIVE_TEMPLATE)
        page = t.render(post=post, title=post.title, published=published)

        archive_file = post.get_archive_file()
        archive_dir  = post.get_archive_dir()
        dest_dir     = make_build_dest_dir(archive_dir)

        f = open(path.join(dest_dir, archive_file), 'w')
        f.write(page)
        f.close()

