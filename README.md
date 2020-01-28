## Introduction
This project is meant for sending license updates to HMRC and receiving usage reporting. Information like license updates
and usage are exchanged as mail attachment between Lite and HMRC

#### Build and Run


##### Without Docker
- To build and run a local Postfix [mail server](https://github.com/uktrade/mailserver)
- To initilize database
`pipenv run ./manage.py migrate`
- To create database superuser `pipenv run ./manage.py createsuperuser`
- To start the application
`pipenv run ./manage.py runserver`

##### With Docker 

An `.env` file is expected at the root of project. An example provided below
```properties
DATABASE_URL=postgresql://postgres:password@lite-hmrc-postgres:5432/postgres
DJANGO_SECRET_KEY='DJANGO_SECRET_KEY'
EMAIL_PASSWORD=password
EMAIL_HOSTNAME=lite-hmrc-ditmail
EMAIL_USER=username
EMAIL_POP3_PORT=995
EMAIL_SMTP_PORT=587
TIME_TESTS=true
LOCK_INTERVAL=120
```
- check out [mailserver](https://github.com/uktrade/mailserver) to a local folder 
has the same parent folder of this repo 
- `docker-compose up --build -d`

if it is the first time building the local environment, a database migration is required to be carried out. 
Run the following command

- `docker exec -it lite-hmrc-intg pipenv run ./manage.py migrate`
- `docker exec -it lite-hmrc-intg pipenv run ./manage.py createsuperuser`

#### Linting
The python code formatter [Black](https://black.readthedocs.io/en/stable/) is used in this project.

To run it: `black .`

To check the format `black --check mail/`

#### Test
