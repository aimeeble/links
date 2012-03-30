class ShortURL(object):
   REDIR = 1
   IMG = 2
   TEXT = 3

   def __init__(self, short_code, short_url, long_url):
      self.short_code = short_code
      self.short_url = short_url
      self.long_url = long_url

      self.link_type = ShortURL.REDIR
      self.mime_type = None

      self.count = 0
      self.refers = {}
      self.ips = {}

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
