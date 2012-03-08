import flask

BASE_URL="http://a/"
CHARS = "123456789abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ"
LEN = len(CHARS)

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

def shorten(full_url):
   """Shortens the full_url into a new short URL.
   """
   global next_id, db
   my_id = next_id
   next_id += 1

   db[my_id] = new_entry(full_url)
   return BASE_URL + codify(my_id)

def new_entry(fullurl):
   return {
      "url": fullurl,
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
@app.route("/", methods = ["GET", "POST"])
def index():
   short_url = ""

   # Handle new data.
   if flask.request.method == "POST":
      if "full_url" not in flask.request.form:
         return flask.make_response("Bad Request", 400)
      full_url = flask.request.form["full_url"]

      short_url = shorten(full_url);

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

   return flask.make_response("Moved", 302, {"Location": entry["url"]})

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

##############################################################################
# Image handling
@app.route("/img/new", methods = ["PUT"])
def put_image():
   return "new img"

@app.route("/img/<imgid>", methods = ["GET"])
def get_image(imgid):
   return "none"

if __name__ == '__main__':
   db[0] = new_entry("http://www.google.com")
   app.run(debug=True,host='0.0.0.0')
