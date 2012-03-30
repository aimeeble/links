
class ApiCommon(object):
   def __init__(self):
      self.sdb = None

   def set_sdb(self, sdb):
      self.sdb = sdb

   def get_sdb(self):
      return self.sdb

apis = ApiCommon()
