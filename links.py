import os
import errno
import uuid
import time
import urllib
import tempfile

import flask
import werkzeug
import pygeoip

import linkapi
from linklib.db import ShortDB
from linklib.db import ShortDBMongo
from linklib.db import ShortInvalidException
from linklib.url import ShortURL
from linklib.util import UploadedFile


BASE_URL = "http://localhost:5000/"

app = flask.Flask(__name__)
sdb = ShortDBMongo(BASE_URL, host="localhost", db="links")

linkapi.apis.set_sdb(sdb)
app.register_blueprint(linkapi.v1, url_prefix='/api/v1')
app.register_blueprint(linkapi.twitpic, url_prefix='/api/twitpic')


def args2qs(args):
    if not args:
        return None
    r = ''
    for key, vals in args.iterlists():
        for val in vals:
            r += '&%s=%s' % (urllib.quote_plus(key), urllib.quote_plus(val))
    return '?' + r[1:]


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

    # Update stats
    remote = flask.request.remote_addr
    referrer = "direct"
    if "referer" in flask.request.headers:
        referrer = flask.request.headers["referer"]
    hit_data = {
        "remote_addr": flask.request.remote_addr,
        "referrer": referrer,
        "time": time.time(),
        "agent": flask.request.headers.get("user-agent"),
        "method": flask.request.method,
        "qs": args2qs(flask.request.args),
        "path": path,
    }
    sdb.record_hit(surl.get_short_code(), hit_data)

    # Redirect
    if surl.is_redir():
        if path:
            dest_url = "%s/%s" % (surl.get_long_url(), path)
        else:
            dest_url = surl.get_long_url()
        return flask.make_response("Moved", 302, {"Location": dest_url})
    elif surl.is_img():
        data = {
            "img_filename": surl.get_info().get("title"),
            "img_url": surl.get_long_url(),
        }
        return flask.render_template("image.html", data=data)

        return flask.send_file(surl.get_long_url(),
                               mimetype=surl.get_mime_type(),
                               add_etags=False)
    elif surl.is_text():
        lang = ""
        print flask.request.args
        if "lang" in flask.request.args:
            lang = " data-language=\"%s\"" % flask.request.args["lang"]
        with open(surl.get_long_url(), "r") as f:
            s = f.read()
            return flask.render_template("text.html", content=s, language=lang)
    else:
        return flask.make_response("invalid type", 500)


def _isbot(refer, agent):
    '''Try and guess if this represents a bot or not
    '''
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
        return True

    return False


@app.route("/<shortcode>+", methods=["GET"])
def stats(shortcode):
    try:
        surl = sdb.load(shortcode)
    except ShortInvalidException, e:
        return flask.make_response("not found", 404)

    geo = pygeoip.GeoIP('data/GeoIP.dat')
    gic = pygeoip.GeoIP('data/GeoLiteCity.dat')

    LINK_TYPES = {}
    LINK_TYPES[1] = "REDIR"
    LINK_TYPES[2] = "IMG"
    LINK_TYPES[3] = "TEXT"

    info = surl.get_info()
    meta = info.get("meta") if info else None

    params = {
        "title": info.get("title") if info else "Unknown",
        "description": meta.get("description") if meta else "None",
        "contentlength": info.get("length", "???") if info else "???",
        "link_type": LINK_TYPES[surl.get_link_type()],
        "mime_type": surl.get_mime_type(),
        "short_url": surl.get_short_url(),
        "long_url": surl.get_long_url(),
        "short_code": surl.get_short_code(),
        "referrers": {},  # {ref->count}
        "locations": {},  # {IP->count}
        "hits": [],
    }

    # collect the stats
    itr = sdb.list_hits(surl.get_short_code())
    for hit in itr:
        # Referrers
        ref = hit["referrer"]
        if ref not in params["referrers"]:
            params["referrers"][ref] = 0
        params["referrers"][ref] += 1

        hit["bot"] = _isbot(hit["referrer"], hit["agent"])

        # Location (IP)
        ip = hit["remote_addr"]
        if ip not in params["locations"]:
            cc = geo.country_code_by_addr(ip)
            if not cc:
                cc = "??"
            params["locations"][ip] = (cc, 0)
        old = params["locations"][ip]
        params["locations"][ip] = (old[0], old[1] + 1)

        hit["time"] = time.strftime("%Y-%m-%d %H:%M:%S",
                                    time.localtime(hit["time"]))

        cc = geo.country_code_by_addr(hit["remote_addr"])
        hit["cc"] = cc if cc else "??"

        area = gic.record_by_addr(ip)
        hit["area"] = area

        params["hits"] += [hit]

    return flask.render_template("stats.html", p=params)


@app.route("/new", methods=["GET"])
def new():
    return flask.render_template("index.html", short_url=None, base=BASE_URL)


@app.route("/new_paste", methods=["POST"])
def new_paste():
    if "p" not in flask.request.form:
        return flask.make_response("Bad Request", 400)

    text = flask.request.form["p"]

    with tempfile.TemporaryFile() as tmp_fh:
        tmp_fh.write(text)
        tmp_fh.seek(0)

        uploaded_file = UploadedFile(flask.request,
                                     stream=tmp_fh,
                                     filename='stdin')
        uploaded_file.save()

        fullpath = uploaded_file.get_filename()

    surl = sdb.new(fullpath)
    surl.link_type = ShortURL.TEXT
    surl.mime_type = "text/plain"
    sdb.save(surl)

    short_url = surl.get_short_url()

    return "%s\n" % short_url


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', threaded=True)
