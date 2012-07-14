import flask
from common import apis
from linklib.db import ShortDB
from linklib.url import ShortURL
from util import jsonify
from werkzeug import secure_filename
import urllib2
import urllib2_file
import json
import tempfile
import os

api = flask.Blueprint('twitpic', __name__)


def _verify_oauth(url, authorization):
   """Forwards the oauth authorization header to the specified URL to validate
   it.

   """
   req = urllib2.Request(url, headers={'Authorization': authorization})
   con = urllib2.urlopen(req)
   body = con.read()

   if 200 != con.getcode():
      return None

   body = json.loads(body)
   return body


def _post(filename):
   sdb = apis.get_sdb()

   with open(filename, "r") as fh:
      url = "%sapi/v1/post" % sdb.prefix

      data = {
            "file": {
               "fd": fh,
               "filename": "%s" % os.path.basename(filename),
            },
         }

      req = urllib2.Request(url, data)
      con = urllib2.urlopen(req)
      body = con.read()

      if 200 != con.getcode():
         return None

      body = json.loads(body)
      return body


@api.route("/shorten", methods = ["GET"])
@jsonify
def shorten():
   sdb = apis.get_sdb()
   q = flask.request.args

   if "u" not in q:
      return None

   full_url = q.get("u")
   surl = sdb.new(full_url)
   surl.link_type = ShortURL.REDIR
   surl.mime_type = surl.info["mimetype"] if surl.info else None
   sdb.save(surl)

   return {"shorturl": surl.get_short_url()}


@api.route("/upload", methods = ["POST"])
def upload():
   return upload_fmt('json')


@api.route("/upload.<fmt>", methods = ["POST"])
@jsonify
def upload_fmt(fmt):
   form = flask.request.form
   files = flask.request.files
   headers = flask.request.headers

   skip_auth = False
   if "skip_auth" in flask.request.args:
      skip_auth = True

   if fmt != 'json':
      raise Exception("We only support json")

   if "message" not in form:
      raise Exception("message missing")

   if "media" not in files:
      raise Exception("media missing")

   # Verify
   if skip_auth:
      twit_info = {
            "screen_name": "unknown",
            "id": "unknown",
         }
   else:
      if "X-Auth-Service-Provider" not in headers:
         raise Exception("OAuth service provider missing")

      if "X-Verify-Credentials-Authorization" not in headers:
         raise Exception("OAuth creds missing")

      twit_info = _verify_oauth(headers["X-Auth-Service-Provider"],
                              headers["X-Verify-Credentials-Authorization" ])
      if not twit_info:
         raise Exception("failed oauth echo")

   file = files["media"]

   # Temporarily save to disk
   tmp_dir = tempfile.mkdtemp(suffix='links')
   tmp_filename = None
   res = None
   try:
      sec_filename = secure_filename(file.filename)
      tmp_filename = os.path.join(tmp_dir, sec_filename)
      mime_type = file.content_type
      file.save(tmp_filename)

      # Post to shortening service
      res = _post(tmp_filename)

      if not res:
         raise Exception("failed to post/shorten file")

   finally:
      # Cleanup temp file
      try:
         os.unlink(tmp_filename)
         os.rmdir(tmp_dir)
      except Exception, e:
         print "failed to unlink: %s" % (str(e))

   result = {
         "id": res["short_code"],
         "text": form["message"],
         "url": res["short_url"],
         "type": mime_type,
         "timestamp": "Wed, 05 May 2010 16:11:48 +0000",
         "user": {
            "id": twit_info["id"],
            "screen_name": twit_info["screen_name"],
         },
      }

   return result

