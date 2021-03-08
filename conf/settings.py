"""
Django settings for conf project.

Generated by 'django-admin startproject' using Django 2.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""
import json
import os
import sys
import uuid

from environ import Env

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENV_FILE = os.path.join(BASE_DIR, ".env")
if os.path.exists(ENV_FILE):
    Env.read_env(ENV_FILE)

env = Env(
    ALLOWED_HOSTS=(str, ""),
    DEBUG=(bool, False),
    LOG_LEVEL=(str, "INFO"),
    HAWK_AUTHENTICATION_ENABLED=(bool, False),
    BACKGROUND_TASK_ENABLED=(bool, True),
    INBOX_POLL_INTERVAL=(int, 300),
    LITE_LICENCE_DATA_POLL_INTERVAL=(int, 1200),
    EMAIL_AWAITING_REPLY_TIME=(int, 3600),
    EMAIL_AWAITING_CORRECTIONS_TIME=(int, 3600),
    NOTIFY_USERS=(str, "[]"),
)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("DJANGO_SECRET_KEY")
DJANGO_SECRET_KEY = env("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = "*"


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "background_task",
    "mail.apps.MailConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "conf.middleware.LoggingMiddleware",
    "conf.middleware.HawkSigningMiddleware",
]

ROOT_URLCONF = "conf.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "conf.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {"default": env.db()}

ENABLE_MOCK_HMRC_SERVICE = env.bool("ENABLE_MOCK_HMRC_SERVICE", False)
if ENABLE_MOCK_HMRC_SERVICE:
    INSTALLED_APPS += ["mock_hmrc.apps.MockHmrcConfig"]

INCOMING_EMAIL_PASSWORD = env("INCOMING_EMAIL_PASSWORD")
INCOMING_EMAIL_HOSTNAME = env("INCOMING_EMAIL_HOSTNAME")
INCOMING_EMAIL_USER = env("INCOMING_EMAIL_USER")
INCOMING_EMAIL_POP3_PORT = env("INCOMING_EMAIL_POP3_PORT")
INCOMING_EMAIL_SMTP_PORT = env("INCOMING_EMAIL_SMTP_PORT")

HMRC_TO_DIT_EMAIL_PASSWORD = env("HMRC_TO_DIT_EMAIL_PASSWORD")
HMRC_TO_DIT_EMAIL_HOSTNAME = env("HMRC_TO_DIT_EMAIL_HOSTNAME")
HMRC_TO_DIT_EMAIL_USER = env("HMRC_TO_DIT_EMAIL_USER")
HMRC_TO_DIT_EMAIL_POP3_PORT = env("HMRC_TO_DIT_EMAIL_POP3_PORT")
HMRC_TO_DIT_EMAIL_SMTP_PORT = env("HMRC_TO_DIT_EMAIL_SMTP_PORT")

OUTGOING_EMAIL_USER = env("OUTGOING_EMAIL_USER")

MOCK_HMRC_EMAIL_PASSWORD = env("MOCK_HMRC_EMAIL_PASSWORD")
MOCK_HMRC_EMAIL_HOSTNAME = env("MOCK_HMRC_EMAIL_HOSTNAME")
MOCK_HMRC_EMAIL_USER = env("MOCK_HMRC_EMAIL_USER")
MOCK_HMRC_EMAIL_POP3_PORT = env("MOCK_HMRC_EMAIL_POP3_PORT")
MOCK_HMRC_EMAIL_SMTP_PORT = env("MOCK_HMRC_EMAIL_SMTP_PORT")

SPIRE_STANDIN_EMAIL_PASSWORD = env("SPIRE_STANDIN_EMAIL_PASSWORD")
SPIRE_STANDIN_EMAIL_HOSTNAME = env("SPIRE_STANDIN_EMAIL_HOSTNAME")
SPIRE_STANDIN_EMAIL_USER = env("SPIRE_STANDIN_EMAIL_USER")
SPIRE_STANDIN_EMAIL_POP3_PORT = env("SPIRE_STANDIN_EMAIL_POP3_PORT")
SPIRE_STANDIN_EMAIL_SMTP_PORT = env("SPIRE_STANDIN_EMAIL_SMTP_PORT")

EMAIL_PASSWORD = env("EMAIL_PASSWORD")
EMAIL_HOSTNAME = env("EMAIL_HOSTNAME")
EMAIL_USER = env("EMAIL_USER")
EMAIL_POP3_PORT = env("EMAIL_POP3_PORT")
EMAIL_SMTP_PORT = env("EMAIL_SMTP_PORT")
SPIRE_ADDRESS = env("SPIRE_ADDRESS")
HMRC_ADDRESS = env("HMRC_ADDRESS")

SPIRE_ADDRESS_PARALLEL_RUN = env("SPIRE_ADDRESS_PARALLEL_RUN")

TIME_TESTS = env("TIME_TESTS")

LOCK_INTERVAL = float(env("LOCK_INTERVAL"))

INBOX_POLL_INTERVAL = env("INBOX_POLL_INTERVAL")
LITE_LICENCE_DATA_POLL_INTERVAL = env("LITE_LICENCE_DATA_POLL_INTERVAL")
EMAIL_AWAITING_REPLY_TIME = env("EMAIL_AWAITING_REPLY_TIME")
EMAIL_AWAITING_CORRECTIONS_TIME = env("EMAIL_AWAITING_CORRECTIONS_TIME")
NOTIFY_USERS = json.loads(env("NOTIFY_USERS"))

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]

SYSTEM_INSTANCE_UUID = uuid.uuid4()

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

if "test" not in sys.argv:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "(asctime)(levelname)(message)(filename)(lineno)(threadName)(name)(thread)(created)(process)(processName)(relativeCreated)(module)(funcName)(levelno)(msecs)(pathname)",  # noqa
            }
        },
        "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
        "loggers": {"": {"handlers": ["console"], "level": env("LOG_LEVEL").upper()}},
    }
else:
    LOGGING = {"version": 1, "disable_existing_loggers": True}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = "/static/"

# HAWK
HAWK_AUTHENTICATION_ENABLED = env("HAWK_AUTHENTICATION_ENABLED")
HAWK_RECEIVER_NONCE_EXPIRY_SECONDS = 60
HAWK_ALGORITHM = "sha256"
HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS = "hmrc-integration"
HAWK_CREDENTIALS = {
    HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS: {
        "id": HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS,
        "key": env("LITE_HMRC_INTEGRATION_HAWK_KEY"),
        "algorithm": HAWK_ALGORITHM,
    },
    "lite-api": {"id": "lite-api", "key": env("LITE_API_HAWK_KEY"), "algorithm": HAWK_ALGORITHM},
}

LITE_API_URL = env("LITE_API_URL")
LITE_API_REQUEST_TIMEOUT = 60  # Maximum time, in seconds, to wait between bytes of a response

# Background Tasks
BACKGROUND_TASK_ENABLED = env("BACKGROUND_TASK_ENABLED")
BACKGROUND_TASK_RUN_ASYNC = True
# Number of times a task is retried given a failure occurs with exponential back-off = ((current_attempt ** 4) + 5)
MAX_ATTEMPTS = 7  # e.g. 7th attempt occurs approx 40 minutes after 1st attempt (assuming instantaneous failures)

# Sentry
if env.str("SENTRY_DSN", ""):
    sentry_sdk.init(
        dsn=env.str("SENTRY_DSN"),
        environment=env.str("SENTRY_ENVIRONMENT"),
        integrations=[DjangoIntegration()],
        send_default_pii=True,
    )

# Application Performance Monitoring
if env.str("ELASTIC_APM_SERVER_URL", ""):
    ELASTIC_APM = {
        "SERVICE_NAME": env.str("ELASTIC_APM_SERVICE_NAME", "lite-hmrc"),
        "SECRET_TOKEN": env.str("ELASTIC_APM_SECRET_TOKEN"),
        "SERVER_URL": env.str("ELASTIC_APM_SERVER_URL"),
        "ENVIRONMENT": env.str("SENTRY_ENVIRONMENT"),
        "DEBUG": DEBUG,
    }
    INSTALLED_APPS.append("elasticapm.contrib.django")

DEFAULT_ENCODING = "iso-8859-1"
