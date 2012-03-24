from url import ShortURL

ShortInvalidException = Exception

class ShortDB(object):
   CHARS = "123456789abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ"
   LEN = len(CHARS)

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
         mod = my_id % ShortDB.LEN
         c = ShortDB.CHARS[mod]
         res = c + res

         my_id = my_id / ShortDB.LEN
         if my_id == 0:
            break
      return res

   @classmethod
   def decode(cls, short_id):
      """Converts the short_id into a numeric ID.
      """
      res = 0
      for c in short_id:
         num = ShortDB.CHARS.find(c)
         res = res * ShortDB.LEN + num
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
