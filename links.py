import flask
import werkzeug
import os
import errno

BASE_URL="http://a/"
CHARS = "123456789abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ"
LEN = len(CHARS)

REDIR = 1
IMG = 2

app = flask.Flask(__name__)

# Map,
#  {
#     "id": {
#        "url": "full url",
#        "stats": {
#           "count": int,
#        }
#     }
#  }
db = {}

# Next ID that's available
next_id = 1

##############################################################################
# Utilities
def codify(num):
   """Converts the number into a code
   """
   res = ""
   while True:
      mod = num % LEN
      c = CHARS[mod]
      res = c + res

      num = num / LEN
      if num == 0:
         break

   return res

def decodify(rid):
   """Converts the rid into a number code
   """
   res = 0
   for c in rid:
      num = CHARS.find(c)
      res = res * LEN + num
   return res

def shorten(full_url, t = REDIR, m = None):
   """Shortens the full_url into a new short URL.
   """
   global next_id, db
   my_id = next_id
   next_id += 1

   db[my_id] = new_entry(full_url, t, m)
   return BASE_URL + codify(my_id)

def new_entry(fullurl, t = REDIR, m = None):
   return {
      "url": fullurl,
      "type": t,
      "mime": m,
      "stats": {
         "count": 0,
         "refer": {},
         "ip": {},
      },
   }

def get_entry(rid):
   """Looks up the rid in the db and returns the object.
   """
   try:
      num = decodify(rid)
   except:
      return None
   if not num in db.keys():
      return None
   return db[num]

def update_entry(entry, request):
   s = entry["stats"]

   s["count"] += 1

   refer = "direct"
   if "referer" in request.headers:
      refer = request.headers["referer"]
   if refer not in s["refer"]:
      s["refer"][refer] = 0
   s["refer"][refer] += 1

   ip = request.remote_addr
   if ip not in s["ip"]:
      s["ip"][ip] = 0
   s["ip"][ip] += 1

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
         filename = werkzeug.secure_filename(f.filename)

         # put the file in a subdir names after the remote client's IP addr
         subpath = os.path.join(flask.request.remote_addr, filename)
         fullpath = os.path.join("static", subpath)

         try:
            os.makedirs(os.path.dirname(fullpath))
         except OSError as exc:
            if exc.errno == errno.EEXIST:
               pass
            else:
               raise
         f.save(fullpath)

         full_url = fullpath
         t = IMG
         m = f.mimetype
      short_url = shorten(full_url, t, m);

      if flask.request.headers["accept"].find("application/json") >= 0:
         return '{"status": "ok", "short_url": "%s"}' % short_url

   return flask.render_template("index.html", short_url=short_url)

##############################################################################
# URL mappings
@app.route("/<rid>", methods = ["GET"])
def get_resource_id(rid):
   entry = get_entry(rid)
   if not entry:
      return flask.make_response("not found", 404)

   update_entry(entry, flask.request)

   if entry["type"] == REDIR:
      return flask.make_response("Moved", 302, {"Location": entry["url"]})
   elif entry["type"] == IMG:
      return flask.send_file(entry["url"], mimetype=entry["mime"])
   else:
      return flask.make_response("invalid type", 500)

@app.route("/<rid>+", methods = ["GET"])
def get_resource_id_stats(rid):
   entry = get_entry(rid)
   if not entry:
      return flask.make_response("not found", 404)

   return str(entry)

@app.route("/dump", methods = ["GET"])
def dump():
   res = "<pre>"
   for key, val in db.items():
      res += "%s ->\n   %s\n" % (codify(key), val)
   res += "</pre>"
   return res

if __name__ == '__main__':
   db[0] = new_entry("http://www.google.com")
   app.run(debug=True,host='0.0.0.0')
