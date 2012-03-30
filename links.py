import flask
import werkzeug
import os
import errno
import uuid
from linklib.url import ShortURL
from linklib.db import ShortDB
from linklib.db import ShortInvalidException
from linklib.util import Util
import linkapi

BASE_URL="http://ame.io/"

app = flask.Flask(__name__)
sdb = ShortDB(BASE_URL, None)

linkapi.apis.set_sdb(sdb)
app.register_blueprint(linkapi.v1, url_prefix='/api/v1')

@app.route("/<shortcode>", methods = ["GET"])
def forward(shortcode):
   # Look up code
   try:
      surl = sdb.load(shortcode)
   except ShortInvalidException, e:
      return flask.make_response("not found", 404)

   # Update stats
   remote = flask.request.remote_addr
   refer = "direct"
   if "referer" in flask.request.headers:
      refer = flask.request.headers["referer"]
   surl.follow_short_url(flask.request.remote_addr, refer)
   sdb.save(surl)

   # Redirect
   if surl.is_redir():
      return flask.make_response("Moved", 302, {"Location": surl.get_long()})
   elif surl.is_img() or surl.is_text():
      return flask.send_file(surl.get_long(), mimetype=surl.get_mime_type())
   else:
      return flask.make_response("invalid type", 500)

@app.route("/<shortcode>+", methods = ["GET"])
def stats(shortcode):
   try:
      surl = sdb.load(shortcode)
   except ShortInvalidException, e:
      return flask.make_response("not found", 404)
   return str(surl)




@app.route("/new", methods = ["GET", "POST"])
def new():
   short_url = ""
   t = ShortURL.REDIR
   m = None

   # Handle new data.
   if flask.request.method == "POST":
      if "full_url" not in flask.request.form and "imgfile" not in flask.request.files:
         return flask.make_response("Bad Request", 400)

      if "full_url" in flask.request.form and len(flask.request.form["full_url"]) > 0:
         full_url = flask.request.form["full_url"]
      else:
         f = flask.request.files["imgfile"]
         fullpath = Util.get_savable_filename(flask.request)
         f.save(fullpath)

         full_url = fullpath
         t = ShortURL.IMG
         m = f.mimetype

      surl = sdb.new(full_url)
      surl.link_type = t
      surl.mime_type = m
      sdb.save(surl)

      short_url = surl.get_short()

      if flask.request.headers["accept"].find("application/json") >= 0:
         return '{"status": "ok", "short_url": "%s"}' % surl.get_short()

   return flask.render_template("index.html", short_url=short_url, base=BASE_URL)

@app.route("/new_paste", methods = ["POST"])
def new_paste():
   if "p" not in flask.request.form:
      return flask.make_response("Bad Request", 400)

   text = flask.request.form["p"]
   fullpath = Util.get_savable_filename(flask.request)
   with open(fullpath, "w+") as f:
      f.write(text)

   surl = sdb.new(fullpath)
   surl.link_type = ShortURL.TEXT
   surl.mime_type = "text/plain"
   sdb.save(surl)

   short_url = surl.get_short()

   return "%s\n" % surl.get_short()


##############################################################################
# URL mappings
@app.route("/<encoded_short_code>", methods = ["GET"])
def get_resource_id(encoded_short_code):
   try:
      short_code = ShortDB.decode(encoded_short_code)
      surl = sdb.load(short_code)
   except ShortInvalidException, e:
      return flask.make_response("not found", 404)

   remote = flask.request.remote_addr
   refer = "direct"
   if "referer" in flask.request.headers:
      refer = flask.request.headers["referer"]

   surl.follow_short_url(flask.request.remote_addr, refer)
   sdb.save(surl)

   if surl.is_redir():
      return flask.make_response("Moved", 302, {"Location": surl.get_long()})
   elif surl.is_img() or surl.is_text():
      return flask.send_file(surl.get_long(), mimetype=surl.get_mime_type())
   else:
      return flask.make_response("invalid type", 500)

@app.route("/<encoded_short_code>+", methods = ["GET"])
def get_resource_id_stats(encoded_short_code):
   try:
      short_code = ShortDB.decode(encoded_short_code)
      surl = sdb.load(short_code)
   except ShortInvalidException, e:
      return flask.make_response("not found", 404)

   return str(surl)

if __name__ == '__main__':
   app.run(debug=True,host='0.0.0.0')
