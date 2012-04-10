from url import ShortURL
import hashlib
import pymongo

ShortInvalidException = Exception

class ShortDBBase(object):
   def __init__(self, prefix, *args, **kwargs):
      pass

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

class ShortDB(ShortDBBase):
   def __init__(self, prefix, *args, **kwargs):
      self.prefix = prefix
      self.next_id = 0

      self.db = {}

   def save(self, surl):
      """Takes the ShortURL object and saves it to the DB.
      """
      self.db[short_code] = surl

   def load(self, short_code):
      """Loads the info for short_url and returns a ShortURL object.
      """
      if short_code not in self.db.keys():
         raise ShortInvalidException("invalid short URL")

      surl = self.db[short_code]
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

   def __iter__(self):
      return self.db.__iter__()

class ShortDBMongo(ShortDBBase):
   def __init__(self, prefix, *args, **kwargs):
      self.prefix = prefix
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
         },
         True)

   def load(self, short_code):
      cur = self.db.urls.find({"short_code": short_code})
      if cur.count() != 1:
         raise ShortInvalidException("invalid short code")
      row = cur.next()

      return ShortURL(row.get("short_code"),
            row.get("short_url"),
            row.get("long_url"))

   def __iter__(self):
      class _generator:
         def __init__(self, db):
            self.cur = db.urls.find({}, {"short_code": 1})
            print "Generating over %d rows" % self.cur.count()
         def next(self):
            row = self.cur.next()
            return row["short_code"]
      return _generator(self.db)

