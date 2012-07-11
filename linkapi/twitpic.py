import flask
from util import jsonify
from werkzeug import secure_filename
import urllib2
import json
from PIL import Image
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


@api.route("/upload", methods = ["POST"])
def upload():
   return upload_fmt('json')


@api.route("/upload.<fmt>", methods = ["POST"])
@jsonify
def upload_fmt(fmt):
   form = flask.request.form
   files = flask.request.files
   headers = flask.request.headers

   if "X-Auth-Service-Provider" not in headers:
      raise Exception("service provider missing")

   if "X-Verify-Credentials-Authorization" not in headers:
      raise Exception("creds missing")

   if "source" not in form:
      raise Exception("source missing")

   if "message" not in form:
      raise Exception("message missing")

   if "media" not in files:
      raise Exception("media missing")

   # Verify
   twit_info = _verify_oauth(headers["X-Auth-Service-Provider"],
                             headers["X-Verify-Credentials-Authorization" ])
   if not twit_info:
      raise Exception("failed auth")

   file = files["media"]
   sec_file = secure_filename(file.filename)
   mime_type = file.content_type#.split('/')[1]

   file.save(sec_file)
   img = Image.open(sec_file)
   st = os.fstat(img.fp.fileno())

   result = {
         "id": "FAKE",
         "text": form["message"],
         "url": "http://ame.io/FAKE",
         "width": img.size[0],
         "height": img.size[1],
         "size": st.st_size,
         "type": mime_type,
         "timestamp": "Wed, 05 May 2010 16:11:48 +0000",
         "user": {
            "id": twit_info["id"],
            "screen_name": twit_info["screen_name"],
         },
      }

   return result

