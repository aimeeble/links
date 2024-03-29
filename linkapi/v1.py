import time

import flask

from common import apis
from linklib.url import ShortURL
from linklib.db import ShortDB
from linklib.db import ShortInvalidException
from linklib.util import UploadedFile
from util import jsonify

# POST /shrink
#     -> url=full_url
#     <- {"url": full_url, "short_code": short_code, "short_url": short_url}
# POST /post
#     -> d=raw_data,m=mime_type(optional)
#     -> file=file-upload
#     <- {"url": full_url, "short_code": short_code, "short_url": short_url}
# GET  /expand/CODE
#     -> nil
#     <- {"url": full_url, "short_code": short_code, "short_url": short_url}
# GET  /stats/CODE
#     -> nil
#     <- {
#           "referrers": [...],
#           "browsers": [...],
#           "client_ips": [...],
#           "times": [...],
#        }
# GET  /dump
#     -> nil
#     <- [/v1/expand/*]

api = flask.Blueprint('v1', __name__)


@api.route("/shrink", methods=["POST"])
@jsonify
def shrink():
    sdb = apis.get_sdb()
    if "url" not in flask.request.form:
        return {
            "status": "FAIL",
            "text": "No URL param",
        }
    full_url = flask.request.form["url"]

    if full_url.startswith(sdb.prefix):
        # Trying to re-shorting a short URL.
        code = full_url[len(sdb.prefix):]
        surl = sdb.load(code)
        # Re-save to update timestamps on surl
        sdb.save(surl)
    else:
        # Trying to shorten a new URL.
        surl = sdb.new(full_url, ShortURL.REDIR)
        surl.mime_type = surl.info["mimetype"] if surl.info else None
        sdb.save(surl)
        print "Shortened %s to %s" % (surl.get_long_url(), surl.get_short_url())

    return {
        "status": "OK",
        "url": full_url,
        "short_code": surl.get_short_code(),
        "short_url": surl.get_short_url(),
    }


@api.route("/post", methods=["POST"])
@jsonify
def post():
    sdb = apis.get_sdb()
    surl = None

    if "file" in flask.request.files:
        uploaded_file = UploadedFile(flask.request, formfile='file')
        uploaded_file.save()

        full_url = uploaded_file.get_filename()

        surl = sdb.new(full_url, ShortURL.IMG)
        surl.mime_type = uploaded_file.get_mimetype()
        if not surl.info:
            surl.info = {}
        surl.info["title"] = uploaded_file.get_remote_filename()
        sdb.save(surl)

    elif "d" in flask.request.form:
        text = flask.request.form["d"]

        with tempfile.TemporaryFile() as tmp_fh:
            tmp_fh.write(text)
            tmp_fh.seek(0)

            uploaded_file = UploadedFile(flask.request, stream=tmp_fh)
            uploaded_file.save()

            full_url = uploaded_file.get_filename()

        surl = sdb.new(full_url, ShortURL.TEXT)
        if "m" in flask.request.form:
            surl.mime_type = flask.request.form["m"]
        else:
            surl.mime_type = "text/plain"
        sdb.save(surl)
    else:
        raise Exception("missing required field")

    return {
        "status": "OK",
        "url": full_url,
        "short_code": surl.get_short_code(),
        "short_url": surl.get_short_url(),
    }


@api.route("/expand/<short_code>", methods=["GET"])
@jsonify
def expand(short_code):
    sdb = apis.get_sdb()
    surl = None

    try:
        surl = sdb.load(short_code)
    except ShortInvalidException, e:
        return {
            "status": "FAIL",
            "text": "Invalid short code",
        }

    return {
        "status": "OK",
        "url": surl.get_long_url(),
        "short_code": surl.get_short_code(),
        "short_url": surl.get_short_url(),
    }


@api.route("/stats/<short_code>", methods=["GET"])
@jsonify
def stats(short_code):
    sdb = apis.get_sdb()

    try:
        surl = sdb.load(short_code)
    except ShortInvalidException, e:
        return {
            "status": "FAIL",
            "text": "Invalid short code",
        }

    hits = sdb.list_hits(short_code)
    hit_list = []
    for hit in hits:
        hit_list.extend([hit])

    return {
        "status": "OK",
        "url": surl.get_long_url(),
        "short_code": surl.get_short_code(),
        "short_url": surl.get_short_url(),
        "hit_list": hit_list,
    }


@api.route("/dump", methods=["GET"])
@jsonify
def dump():
    sdb = apis.get_sdb()
    res = []

    for short_code in sdb:
        surl = sdb.load(short_code)
        hits = sdb.count_hits(short_code)
        surl_dict = {
            "url": surl.get_long_url(),
            "short_code": surl.get_short_code(),
            "short_url": surl.get_short_url(),
            "hits": hits,
        }
        res.append(surl_dict)

    return {
        "status": "OK",
        "result": res,
    }


@api.route("/activity", methods=["POST"])
@jsonify
def activity():
    if "hit_code" not in flask.request.form:
        return {
            "status": "FAIL",
            "text": "Invalid hit code",
        }
    if "type" not in flask.request.form:
        return {
            "status": "FAIL",
            "text": "Missing activity type",
        }

    hit_code = flask.request.form["hit_code"]
    act_type = flask.request.form["type"]
    stats = {
        "activity": {
            "type": act_type,
            "time": time.time(),
        },
    }

    sdb = apis.get_sdb()
    try:
        sdb.update_hit(hit_code, stats)
    except Exception, e:
        return {
            "status": "FAIL",
            "text": "%s" % (str(e)),
        }

    return {
        "status": "OK",
    }
