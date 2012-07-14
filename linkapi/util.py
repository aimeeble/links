import flask
import json
import functools

def jsonify(f):
   @functools.wraps(f)
   def _wrap(*args, **kwargs):
      try:
         res = f(*args, **kwargs)
         return flask.Response("%s\n" % json.dumps(res),
                              content_type="application/json")
      except Exception, e:
         res = {
               "err": "%s" % (str(e)),
            }
         res = flask.Response("%s\n" % json.dumps(res),
                               content_type="application/json")
         res.status_code = 500
         return res
   return _wrap

