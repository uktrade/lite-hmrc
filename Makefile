alltest:
	pipenv run ./manage.py test -v 2 --exclude-tag=end-to-end

run:
	pipenv run ./manage.py runserver

check-format:
	black --check ./mail

cov:
	pipenv run coverage run --source='.' manage.py test mail --exclude-tag=end-to-end

cov-report:
	pipenv run coverage report
