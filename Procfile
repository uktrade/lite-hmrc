# See gunicorn.conf.py for more configuration.
web: python manage.py migrate && gunicorn conf.wsgi:application
celeryworker: celery -A conf worker -l info
celerybeat: celery -A conf beat -l info
