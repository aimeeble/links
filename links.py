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
import time
import GeoIP

BASE_URL="http://localhost:5000/"

app = flask.Flask(__name__)
sdb = ShortDBMongo(BASE_URL, host="localhost", db="links")

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
   referrer = "direct"
   if "referer" in flask.request.headers:
      referrer = flask.request.headers["referer"]
   hit_data = {
            "remote_addr": flask.request.remote_addr,
            "referrer": referrer,
            "time": time.time(),
            "agent": flask.request.headers.get("user-agent"),
            "method": flask.request.method,
         }
   sdb.record_hit(surl.get_short_code(), hit_data)

   # Redirect
   if surl.is_redir():
      return flask.make_response("Moved", 302, {"Location": surl.get_long_url()})
   elif surl.is_img():
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

@app.route("/<shortcode>+", methods = ["GET"])
def stats(shortcode):
   try:
      surl = sdb.load(shortcode)
   except ShortInvalidException, e:
      return flask.make_response("not found", 404)

   geo = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)

   params = {
         "title": "... url title goes here ...",
         "short_url": surl.get_short_url(),
         "long_url": surl.get_long_url(),
         "short_code": surl.get_short_code(),
         "referrers": {}, # {ref->count}
         "locations": {}, # {IP->count}
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

      # Location (IP)
      ip = hit["remote_addr"]
      if ip not in params["locations"]:
         cc = geo.country_code_by_addr(ip)
         if not cc:
            cc = "??"
         params["locations"][ip] = (cc, 0)
      old = params["locations"][ip]
      params["locations"][ip] = (old[0], old[1] + 1)

      hit["time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(hit["time"]))
      cc = geo.country_code_by_addr(hit["remote_addr"])
      hit["cc"] = cc if cc else "??"
      params["hits"] += [hit]

   return flask.render_template("stats.html", p=params)

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

if __name__ == '__main__':
   app.run(debug=True,host='0.0.0.0')
