alltest:
	pipenv run ./manage.py test -v 2 --exclude-tag=only

run:
	pipenv run ./manage.py runserver

check-format:
	black --check ./mail

cov:
	pipenv run coverage run --source='.' manage.py test mail --exclude-tag=only

cov-report:
	pipenv run coverage report
