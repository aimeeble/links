from url import ShortURL
from stats import ShortHit
import hashlib
import pymongo

ShortInvalidException = Exception

class ShortDBBase(object):
   def __init__(self, prefix):
      self.prefix = prefix

   def _validate_hash(self, hash_code):
      """Validate the hash is not used.  It is common to override this in
      subclasses if they need to query the database or something.
      """
      if hash_code:
         return True
      return False

   def _hash_url(self, long_url):
      """Takes a hash of the URL and, if valid, returns it
      """
      hash_code = None

      while not self._validate_hash(hash_code):
         m = hashlib.md5()
         m.update(long_url)
         hash_code = m.hexdigest()

      return hash_code

   def save(self, surl):
      """Override in a subclass to support saving.
      """
      pass

   def load(self, short_code):
      """Override in a subclass to support loading.
      """
      pass

   def new(self, long_url):
      """Creates and returns a new ShortURL representing the url.
      """
      short_code = self._hash_url(long_url)
      short_url = self.prefix + short_code

      surl = ShortURL(short_code, short_url, long_url)

      self.save(surl)
      return surl

   def record_hit(self, short_code, stats):
      """Records someone following the short-url.
      """
      pass

   def list_hits(self, short_code):
      """Returns a generator for all hits.  The generator should return a dict
      containing the stats at the top level.
      """
      class _foo:
         def __iter__(self):
            return self
         def next(self):
            raise StopIteration()
      return _foo()

class ShortDB(ShortDBBase):
   def __init__(self, prefix, *args, **kwargs):
      super(ShortDB, self).__init__(prefix)
      self.next_id = 0
      self.db = {}
      self.stats = {}

   def save(self, surl):
      """Takes the ShortURL object and saves it to the DB.
      """
      self.db[surl.get_short_code()] = surl

   def load(self, short_code):
      """Loads the info for short_url and returns a ShortURL object.
      """
      if short_code not in self.db.keys():
         raise ShortInvalidException("invalid short URL")

      surl = self.db[short_code]
      return surl

   def __str__(self):
      res = ""
      for surl in self.db.values():
         res += str(surl) + "\n"
      return res

   def __iter__(self):
      return self.db.__iter__()

   def record_hit(self, short_code, stats):
      if short_code not in self.stats:
         self.stats[short_code] = []
      self.stats[short_code].append(stats)

   def list_hits(self, short_code):
      if short_code not in self.stats:
         return super(ShortDB, self).list_hits(short_code)
      return self.stats[short_code]

class ShortDBMongo(ShortDBBase):
   def __init__(self, prefix, *args, **kwargs):
      super(ShortDBMongo, self).__init__(prefix)

      self.host = kwargs.get("host")
      self.db_name = kwargs.get("db")
      self.connection = pymongo.Connection(self.host)
      self.db = pymongo.database.Database(self.connection, self.db_name)

   def _validate_hash(self, hash_code):
      if not hash_code:
         return False

      cur = self.db.urls.find({"short_code": hash_code})
      if cur.count() == 0:
         print "valid: %s" % hash_code
         return True
      print "invalid: %s" % hash_code
      return False

   def save(self, surl):
      self.db.urls.update(
         {
            "short_code": surl.get_short_code(),
         },
         {
            "short_code": surl.get_short_code(),
            "short_url": surl.get_short_url(),
            "long_url": surl.get_long_url(),
            "link_type": surl.get_link_type(),
            "mime_type": surl.get_mime_type(),
         },
         True)

   def load(self, short_code):
      cur = self.db.urls.find({"short_code": short_code})
      if cur.count() != 1:
         raise ShortInvalidException("invalid short code")
      row = cur.next()

      surl = ShortURL(row.get("short_code"),
            row.get("short_url"),
            row.get("long_url"))
      surl.link_type = row.get("link_type")
      surl.mime_type = row.get("mime_type")

      return surl

   def __iter__(self):
      class _generator:
         def __init__(self, db):
            self.cur = db.urls.find({}, {"short_code": 1})
            print "Generating over %d rows" % self.cur.count()
         def next(self):
            row = self.cur.next()
            return row["short_code"]
      return _generator(self.db)

   def record_hit(self, short_code, stats):
      """Records someone following the short-url.
      """
      to_add = {
            "short_code": short_code,
            "stats": stats,
         }
      self.db.hits.insert(to_add)

   def list_hits(self, short_code):
      class _gen:
         def __init__(self, cursor):
            self.cursor = cursor
         def __iter__(self):
            return self
         def next(self):
            row = self.cursor.next()
            return row["stats"]
      cur = self.db.hits.find({"short_code": short_code}, {"stats": 1})
      return _gen(cur)

