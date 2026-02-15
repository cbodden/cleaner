"""Production WSGI entry point.

Use with a production ASGI/WSGI server, e.g.:
  gunicorn -w 4 -b 0.0.0.0:5000 wsgi:application
  uwsgi --http 0.0.0.0:5000 --module wsgi:application
"""
from app import app

application = app
