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
