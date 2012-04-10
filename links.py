import flask
import werkzeug
import os
import errno
import uuid
from linklib.url import ShortURL
from linklib.db import ShortDB
from linklib.db import ShortDBMongo
from linklib.db import ShortInvalidException
from linklib.util import Util
import linkapi

BASE_URL="http://ame.io/"

app = flask.Flask(__name__)
sdb = ShortDBMongo(BASE_URL, host="mongodb", db="links")

linkapi.apis.set_sdb(sdb)
app.register_blueprint(linkapi.v1, url_prefix='/api/v1')

@app.route("/")
def main():
   return ""

@app.route("/<shortcode>", methods = ["GET"])
def forward(shortcode):
   # Look up code
   try:
      surl = sdb.load(shortcode)
   except ShortInvalidException, e:
      return flask.make_response("invalid short code", 404)

   # Update stats
   remote = flask.request.remote_addr
   refer = "direct"
   if "referer" in flask.request.headers:
      refer = flask.request.headers["referer"]
   surl.follow_short_url(flask.request.remote_addr, refer)
   sdb.save(surl)

   # Redirect
   if surl.is_redir():
      return flask.make_response("Moved", 302, {"Location": surl.get_long_url()})
   elif surl.is_img():
      return flask.send_file(surl.get_long_url(), mimetype=surl.get_mime_type())
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

@app.route("/<shortcode>+", methods = ["GET"])
def stats(shortcode):
   try:
      surl = sdb.load(shortcode)
   except ShortInvalidException, e:
      return flask.make_response("not found", 404)
   return str(surl)

@app.route("/new", methods = ["GET"])
def new():
   return flask.render_template("index.html", short_url=None, base=BASE_URL)

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

   short_url = surl.get_short_url()

   return "%s\n" % short_url


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
