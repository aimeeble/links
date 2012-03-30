import flask
import json

def simple_decorator(decorator):
   """This decorator can be used to turn simple functions into well-behaved
   decorators, so long as the decorators are fairly simple. If a decorator
   expects a function and returns a function (no descriptors), and if it
   doesn't modify function attributes or docstring, then it is eligible to use
   this. Simply apply @simple_decorator to your decorator and it will
   automatically preserve the docstring and function attributes of functions to
   which it is applied.
   """
   def new_decorator(f):
      g = decorator(f)
      g.__name__ = f.__name__
      g.__doc__ = f.__doc__
      g.__dict__.update(f.__dict__)
      return g
   # Now a few lines needed to make simple_decorator itself
   # be a well-behaved decorator.
   new_decorator.__name__ = decorator.__name__
   new_decorator.__doc__ = decorator.__doc__
   new_decorator.__dict__.update(decorator.__dict__)
   return new_decorator

@simple_decorator
def jsonify(f):
   def _wrap(*args, **kwargs):
      res = f(*args, **kwargs)
      return flask.Response("%s\n" % json.dumps(res),
                            content_type="application/json")
   return _wrap
