# See gunicorn.conf.py for more configuration.
web: python manage.py migrate && gunicorn conf.wsgi:application
worker: python manage.py process_tasks --log-std
celeryworker: celery -A conf worker -l info
celerybeat: celery -A conf beat -l info
