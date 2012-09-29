import os
import errno
import uuid
import re
import time
import urllib
import tempfile

import flask
import werkzeug

import linkapi
from linklib.db import ShortDB
from linklib.db import ShortDBMongo
from linklib.db import ShortInvalidException
from linklib.url import ShortURL
from linklib.util import UploadedFile
from util import Forwarder
from classify import Classifier


BASE_URL = "http://localhost:5000/"

app = flask.Flask(__name__)
sdb = ShortDBMongo(BASE_URL, host="localhost", db="links")

linkapi.apis.set_sdb(sdb)
app.register_blueprint(linkapi.v1, url_prefix='/api/v1')
app.register_blueprint(linkapi.twitpic, url_prefix='/api/twitpic')


@app.route("/")
def main():
    return ""


@app.route("/<shortcode>", methods=["GET"])
def forward(shortcode):
    return forward_full(shortcode, None)


@app.route("/<shortcode>/<path:path>", methods=["GET"])
def forward_full(shortcode, path):
    # Look up code
    try:
        surl = sdb.load(shortcode)
    except ShortInvalidException, e:
        return flask.make_response("invalid short code", 404)

    fwd = Forwarder(sdb, surl, path)
    return fwd.handle_request()


def _isbot(hit):
    '''Try and guess if this represents a bot or not
    '''
    refer = hit["referrer"]
    agent = hit["agent"]
    res = False

    agent_list = [
        "Twitterbot/1.0",
        "UnwindFetchor/1.0 (+http://www.gnip.com/)",
        "Mozilla/5.0 (compatible; TweetmemeBot/2.11; +http://tweetmeme.com/)",
        "Mozilla/5.0 (compatible; Butterfly/1.0; +http://labs.topsy.com/butterfly/) Gecko/2009032608 Firefox/3.0.8",
        "Mozilla/5.0 (compatible; PaperLiBot/2.1; http://support.paper.li/entries/20023257-what-is-paper-li)",
        "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6 (FlipboardProxy/1.1; +http://flipboard.com/browserproxy)",
        "Mozilla/5.0 (compatible; TweetmemeBot/2.11; +http://tweetmeme.com/)",
        "InAGist URL Resolver (http://inagist.com)",
        "TwitJobSearch.com",
        "Twisted PageGetter",
        "Python-urllib/2.5",
        "Python-urllib/2.6",
        "python-requests/0.9.2",
        "PycURL/7.19.5",
        "MFE_expand/0.1",
        "NING/1.0",
        "MetaURI API/2.0 +metauri.com",
        "Voyager/1.0",
        "JS-Kit URL Resolver, http://js-kit.com/",
        "ScooperBot www.customscoop.com",
        "Twitmunin Crawler http://www.twitmunin.com",
    ]

    if agent in agent_list:
        res = True

    if "activity" in hit:
        res = False

    return res


def _linkify_hashtags_twitter(text):
    base = 'http://twitter.com/#!/search/?src=hash&q=%23'
    return re.sub(r'#([\w_]+)', r'<a href="%s\1">#\1</a>' % base, text)


def _linkify_users_twitter(text):
    base = 'http://twitter.com/'
    return re.sub(r'@(\w{1,15})', r'<a href="%s\1">@\1</a>' % base, text)


def _linkify_links(text):
    return re.sub(r'(https?://[\w./\?&]+)', r'<a href="\1">\1</a>', text)


@app.route("/<shortcode>+", methods=["GET"])
def stats(shortcode):
    try:
        surl = sdb.load(shortcode)
    except ShortInvalidException, e:
        return flask.make_response("not found", 404)

    # tiny thumb?
    thumb = None
    if surl.get_link_type() == ShortURL.IMG and \
            surl.get_mime_type().find('image') != -1:
        thumb = Forwarder._thumbify(surl.get_long_url(), tiny=True)

    params = {
        "title": surl.get_title(),
        "description": surl.get_description(),
        "contentlength": surl.get_content_length() or "???",
        "link_type": surl.get_link_type_text(),
        "mime_type": surl.get_mime_type(),
        "short_url": surl.get_short_url(),
        "long_url": surl.get_long_url(),
        "short_code": surl.get_short_code(),
        "referrers": {},  # {ref->count}
        "locations": {},  # {IP->count}
        "hits": [],
        "social": surl.get_social(),
        "thumb": thumb,
    }

    # collect the stats
    itr = sdb.list_hits(surl.get_short_code())
    for hit in itr:
        classifier = Classifier(sdb, surl, hit)
        # Referrers
        ref = hit["referrer"]
        if ref not in params["referrers"]:
            params["referrers"][ref] = 0
        params["referrers"][ref] += 1

        hit["bot"] = classifier.is_bot()

        hit["time"] = time.strftime("%Y-%m-%d %H:%M:%S",
                                    time.localtime(hit["time"]))
        hit["reltime"] = "2h"

        hit["cc"] = classifier.get_country_code('??')
        hit["area"] = classifier.get_region('??')

        params["hits"] += [hit]

    # Process social
    for post in params.get("social", {}).get('posts', []):
        post["when"] = time.strftime("%Y-%m-%d %H:%M:%S",
                                     time.localtime(post["when"]))
        # Linkify URLs
        post['text'] = _linkify_links(post['text'])
        # Linkify twitter stuff
        if post['source'] == 'twitter':
            post['text'] = _linkify_hashtags_twitter(post['text'])
            post['text'] = _linkify_users_twitter(post['text'])

    return flask.render_template("stats.html", p=params)


@app.route("/new", methods=["GET"])
def new():
    return flask.render_template("index.html", short_url=None, base=BASE_URL)


@app.route("/new_paste", methods=["POST"])
def new_paste():
    if "p" not in flask.request.form:
        return flask.make_response("Bad Request", 400)

    text = flask.request.form["p"]
    title = flask.request.form.get("title")
    lang = flask.request.form.get("lang")

    with tempfile.TemporaryFile() as tmp_fh:
        tmp_fh.write(text)
        tmp_fh.seek(0)

        uploaded_file = UploadedFile(flask.request,
                                     stream=tmp_fh,
                                     filename='stdin')
        uploaded_file.save()

        fullpath = uploaded_file.get_filename()

    surl = sdb.new(fullpath)
    surl.get_info()["title"] = title
    surl.get_info()["lang"] = lang
    surl.link_type = ShortURL.TEXT
    surl.mime_type = "text/plain"
    sdb.save(surl)

    short_url = surl.get_short_url()

    return "%s\n" % short_url


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', threaded=True)
