import uuid
import os
import errno
import urllib2
import bs4

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

class HeadRequest(urllib2.Request):
   def get_method(self):
      return "HEAD"

def get_page_info(url):
   info = {}

   # Start by getting head.  We only do fancy stuff when it's the right type.
   res = urllib2.urlopen(HeadRequest(url))
   if res.headers.gettype() != "text/html":
      info["mimetype"] = res.headers.gettype()
      length = res.headers.get("Content-length")
      if length:
         info["length"] = length
      return info

   # This makes the assumption that HTML files are small, so we fetch it all.
   res = urllib2.urlopen(url)
   html = res.read()
   soup = bs4.BeautifulSoup(html, "lxml")

   if soup.title:
      info["title"] = soup.title.get_text(strip=True)

   info["meta"] = {}
   for meta in soup.find_all("meta"):
      key = meta.get("name")
      val = meta.get("content")
      if key and val:
         key = key.replace(".", "_")
         info["meta"][key] = val

   info["mimetype"] = res.headers.gettype()
   length = res.headers.get("Content-length")
   if length:
      info["length"] = length

   return info
