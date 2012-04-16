import flask
import json
import functools

def jsonify(f):
   @functools.wraps(f)
   def _wrap(*args, **kwargs):
      res = f(*args, **kwargs)
      return flask.Response("%s\n" % json.dumps(res),
                            content_type="application/json")
   return _wrap

