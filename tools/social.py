#!/usr/bin/python

import json
import sys
import time
import urllib2
sys.path.insert(0, ".")

#from links import BASE_URL
BASE_URL = 'http://ame.io/'
from linklib.db import ShortDBMongo
from linklib.url import ShortURL


class Engine(object):
    SOURCES = []

    def __init__(self):
        self.sdb = ShortDBMongo(BASE_URL, host='localhost', db='links')

        self.src_objs = []
        for src_class in Engine.SOURCES:
            src_obj = src_class()
            self.src_objs.append(src_obj)

    def _find_posts(self, surl):
        short_url = surl.get_short_url()
        print 'Scanning for %s...' % (short_url)

        social = surl.get_social()
        posts = social.get('posts', [])
        sinces = social.get('sinces', {})

        for src in self.src_objs:
            name = src.get_name()

            print '\tpolling %s' % (name)
            since = None
            if name in sinces:
                since = sinces[name]

            print '\t\tsince = %s' % (since)
            new_posts = src.find(short_url, since)

            posts.extend(new_posts)
            sinces[name] = src.get_since()

        social['posts'] = posts
        social['sinces'] = sinces

        return social

    def _process_code(self, short_code):
        surl = self.sdb.load(short_code)

        self._find_posts(surl)
        self.sdb.save(surl, update_time=False)

    def run(self, count=-1):
        num_done = 0

        for short_code in self.sdb:
            self._process_code(short_code)

            num_done += 1
            if count > 0 and num_done >= count:
                return


class MetaRegister(type):
    def __new__(cls, name, bases, dct):
        t = type.__new__(cls, name, bases, dct)
        if name != 'SourceBase':
            Engine.SOURCES.append(t)
        return t


class SourceBase(object):
    __metaclass__ = MetaRegister


class FakeSource(SourceBase):
    def get_since(self):
        return 5

    def get_name(self):
        return 'fake'

    def find(self, short_url, since=None):
        return []


class Twitter(SourceBase):
    def __init__(self):
        self.since = None

    def get_since(self):
        return self.since

    def get_name(self):
        return 'twitter'

    def _test_find(self, short_url, since=None):
        user = 'aimeeble'
        post_id = 231293851195809793

        fake_result = {
            'source': self.get_name(),
            'id': post_id,

            'handle': '%s' % user,
            'url': 'http://www.twitter.com/%s/status/%u' % (user, post_id),
            'text': 'foo bar baz (#hash) #hash #foo_bar #hash&hash #hash42 #42has #12 #hash! @user (@user) @user! @user123 @user_name',
            'when': time.time(),
            'img_url': 'http://a0.twimg.com/profile_images/2171549983/me-2012-04-23_normal.jpg',
        }

        self.since = 9123

        return [fake_result]

    def _real_find(self, short_url, since=None):
        url = 'http://search.twitter.com/search.json?q=%s' % (urllib2.quote(short_url))
        if since:
            url += '&since_id=%s' % (since)
        print '\t\t%s' % url

        req = urllib2.Request(url)
        res = urllib2.urlopen(req)

        dct = json.loads(res.read())
        tweets = []
        for tweet in dct['results']:
            my_format = {
                'source': self.get_name(),
                'id': tweet['id'],

                'handle': tweet['from_user'],
                'url': 'http://www.twitter.com/%s/status/%u' % (tweet['from_user'], tweet['id']),
                'text': tweet['text'],
                'when': time.time(),
                'img_url': tweet['profile_image_url'],
            }
            tweets.append(my_format)

        self.since = dct['max_id']

        return tweets

    find = _real_find
    #find = _test_find


if __name__ == '__main__':
    e = Engine()
    e.run(count=15)
