alltest:
	pipenv run ./manage.py test -v 2

run:
	pipenv run ./manage.py runserver
