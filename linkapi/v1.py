import flask
from util import jsonify
from common import apis
from linklib.url import ShortURL
from linklib.db import ShortDB
from linklib.db import ShortInvalidException
from linklib.util import Util

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
#     <- {"referrers": [...], "browsers": [...], "client_ips": [...], "times": [...]}
# GET  /dump
#     -> nil
#     <- [/v1/expand/*]

api = flask.Blueprint('v1', __name__)

@api.route("/shrink", methods = ["POST"])
@jsonify
def shrink():
   sdb = apis.get_sdb()
   if "url" not in flask.request.form:
      return {
            "status": "FAIL",
            "text": "No URL param",
         }

   full_url = flask.request.form["url"]
   surl = sdb.new(full_url)
   surl.link_type = ShortURL.REDIR
   surl.mime_type = surl.info["mimetype"] if surl.info else None
   sdb.save(surl)

   return {
         "status": "OK",
         "url": full_url,
         "short_code": surl.get_short_code(),
         "short_url": surl.get_short_url(),
      }

@api.route("/post", methods = ["POST"])
@jsonify
def post():
   sdb = apis.get_sdb()
   surl = None

   if "file" in flask.request.files:
      f = flask.request.files["file"]
      rel_path = Util.get_savable_filename(flask.request)
      f.save(rel_path)

      full_url = rel_path

      surl = sdb.new(full_url)
      surl.link_type = ShortURL.IMG
      surl.mime_type = f.mimetype
      if not surl.info:
         surl.info = {}
      surl.info["title"] = f.filename
      sdb.save(surl)

   elif "d" in flask.request.form:
      text = flask.request.form["d"]
      rel_path = Util.get_savable_filename(flask.request)

      full_url = rel_path

      with open(rel_path, "w+") as f:
         f.write(text)

      surl = sdb.new(full_url)
      surl.link_type = ShortURL.TEXT
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

@api.route("/expand/<short_code>", methods = ["GET"])
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

@api.route("/stats/<short_code>", methods = ["GET"])
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

@api.route("/dump", methods = ["GET"])
@jsonify
def dump():
   sdb = apis.get_sdb()
   res = []

   for short_code in sdb:
      surl = sdb.load(short_code)
      surl_dict = {
            "url": surl.get_long_url(),
            "short_code": surl.get_short_code(),
            "short_url": surl.get_short_url(),
         }
      res.append(surl_dict)

   return {
         "status": "OK",
         "result": res,
      }

