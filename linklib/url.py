import time


class ShortURL(object):
   REDIR = 1
   IMG = 2
   TEXT = 3

   def __init__(self, short_code, short_url, long_url=None, info={}):
      self.short_code = short_code
      self.short_url = short_url
      self.long_url = long_url
      self.info = info
      self.latest_short = time.time()

      self.link_type = ShortURL.REDIR
      self.mime_type = None
      self.qs = None

   def get_link_type(self):
      return self.link_type

   def is_redir(self):
      return self.link_type == ShortURL.REDIR

   def is_img(self):
      return self.link_type == ShortURL.IMG

   def is_text(self):
      return self.link_type == ShortURL.TEXT

   def get_mime_type(self):
      return self.mime_type

   def get_short_code(self):
      return self.short_code

   def get_short_url(self):
      return self.short_url

   def get_long_url(self):
      return self.long_url

   def get_info(self):
      return self.info

   def __str__(self):
      return "(URL %s = %s)" % (self.short_code, self.long_url)

   def serialize(self):
      return {
         "short_code": self.short_code,
         "long_url": self.long_url,
         "link_type": self.link_type,
         "mime_type": self.mime_type,
         "info": self.info,
         "latest_short": time.time()
      }

   def deserialize(self, data):
      self.short_code = data.get("short_code")
      self.long_url = data.get("long_url")
      self.link_type = data.get("link_type")
      self.mime_type = data.get("mime_type")
      self.info = data.get("info")
      self.latest_short = data.get("latest_short")
