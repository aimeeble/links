from url import ShortURL
import hashlib

ShortInvalidException = Exception

class ShortDB(object):
   def __init__(self, prefix, db_url):
      self.prefix = prefix
      self.db_url = db_url
      self.next_id = 0

      self.db = {}

   def _hash_url(self, long_url):
      m = hashlib.md5()
      m.update(long_url)
      return m.hexdigest()

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
      short_code = self._hash_url(long_url)
      short_url = self.prefix + short_code

      surl = ShortURL(short_code, short_url, long_url)

      self.db[short_code] = surl
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

