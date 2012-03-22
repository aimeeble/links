import flask
import werkzeug
import os
import errno
import uuid

BASE_URL="http://ame.io/"
CHARS = "123456789abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ"
LEN = len(CHARS)

REDIR = 1
IMG = 2

class ShortURL(object):
   def __init__(self, short_id, short_url, long_url):
      self.short_id = short_id
      self.short_url = short_url
      self.long_url = long_url

      self.link_type = REDIR
      self.mime_type = None

      self.count = 0
      self.refers = {}
      self.ips = {}

   def is_redir(self):
      return self.link_type == REDIR

   def is_img(self):
      return self.link_type == IMG

   def get_mime_type(self):
      return self.mime_type

   def get_short(self):
      return self.short_url

   def get_long(self):
      return self.long_url

   def follow_short_url(self, remote_ip, referer):
      """Updates the stats after someone followed this URL.
      """
      self.count += 1

      if referer not in self.refers:
         self.refers[referer] = 1
      else:
         self.refers[referer] += 1

      if remote_ip not in self.ips:
         self.ips[remote_ip] = 1
      else:
         self.ips[remote_ip] += 1

   def __str__(self):
      return "(URL %s -> %s :: count:%s, IPs:%s, Refers:%s)" % \
            (self.short_url, self.long_url, self.count, self.ips, self.refers)

ShortInvalidException = Exception

class ShortDB(object):
   def __init__(self, prefix, db_url):
      self.prefix = prefix
      self.db_url = db_url
      self.next_id = 0

      self.db = {}

   @classmethod
   def encode(cls, my_id):
      """Converts my_id into a code for use in the short URL.
      """
      res = ""
      while True:
         mod = my_id % LEN
         c = CHARS[mod]
         res = c + res

         my_id = my_id / LEN
         if my_id == 0:
            break
      return res

   @classmethod
   def decode(cls, short_id):
      """Converts the short_id into a numeric ID.
      """
      res = 0
      for c in short_id:
         num = CHARS.find(c)
         res = res * LEN + num
      return res

   def get_new_id(self):
      my_id = self.next_id
      self.next_id += 1
      return my_id

   def _shorten(self, my_id, long_url):
      """Returns a complete shortened URL.
      """
      return self.prefix + ShortDB.encode(my_id)

   def save(self, short_url_obj):
      """Takes the ShortURL object and saves it to the DB.
      """
      pass

   def load(self, short_code):
      """Loads the info for short_url and returns a ShortURL object.
      """
      if short_code not in self.db.keys():
         raise ShortInvalidException("invalid short URL")

      surl = self.db[short_code]
      return surl

   def new(self, long_url):
      """Creates and returns a new ShortURL representing the url.
      """
      my_id = self.get_new_id()
      short_url = self._shorten(my_id, long_url)

      surl = ShortURL(my_id, short_url, long_url)

      self.db[my_id] = surl
      return surl

   def save(self, surl):
      """Saves updates made to the ShortURL object.
      """
      pass

   def __str__(self):
      res = ""
      for surl in self.db.values():
         res += str(surl) + "\n"
      return res

class Util(object):
   @classmethod
   def _create_paths(cls, fullpath):
      try:
         os.makedirs(os.path.dirname(fullpath))
      except OSError as exc:
         if exc.errno == errno.EEXIST:
            pass
         else:
            raise

   @classmethod
   def get_savable_filename(cls, req):
      filename = str(uuid.uuid4())

      # put the file in a subdir names after the remote client's IP addr
      subpath = os.path.join(req.remote_addr, filename)
      fullpath = os.path.join("static", subpath)

      Util._create_paths(fullpath)
      return fullpath

app = flask.Flask(__name__)
sdb = ShortDB(BASE_URL, None)


##############################################################################
# Landing page and creation
@app.route("/")
def index():
   return flask.make_response("Nothing", 404)

@app.route("/new", methods = ["GET", "POST"])
def new():
   short_url = ""
   t = REDIR
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
         t = IMG
         m = f.mimetype

      surl = sdb.new(full_url)
      surl.link_type = t
      surl.mime_type = m
      sdb.save(surl)

      short_url = surl.get_short()

      if flask.request.headers["accept"].find("application/json") >= 0:
         return '{"status": "ok", "short_url": "%s"}' % surl.get_short()

   return flask.render_template("index.html", short_url=short_url, base=BASE_URL)

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
   elif surl.is_img():
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

@app.route("/dump", methods = ["GET"])
def dump():
   return "<pre>%s</pre>" % str(sdb)

if __name__ == '__main__':
   sdb.new("http://www.google.com")
   app.run(debug=True,host='0.0.0.0')
