import os
import sys
import uuid
from pathlib import Path
from urllib.parse import urlencode

import dj_database_url
import sentry_sdk
from dbt_copilot_python.database import database_url_from_env
from dbt_copilot_python.network import setup_allowed_hosts
from dbt_copilot_python.utility import is_copilot
from django_log_formatter_asim import ASIMFormatter
from django_log_formatter_ecs import ECSFormatter
from environ import Env
from sentry_sdk.integrations.django import DjangoIntegration

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENV_FILE = os.path.join(BASE_DIR, ".env")
if os.path.exists(ENV_FILE):
    Env.read_env(ENV_FILE)

env = Env()

VCAP_SERVICES = env.json("VCAP_SERVICES", {})

IS_ENV_DBT_PLATFORM = is_copilot()
IS_ENV_GOV_PAAS = bool(VCAP_SERVICES)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("DJANGO_SECRET_KEY")
DJANGO_SECRET_KEY = env("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "mail",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    "health_check.contrib.celery",
    "health_check.contrib.celery_ping",
    "django_db_anonymiser.db_anonymiser",
    "healthcheck",
    "health_check.contrib.migrations",
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


ENABLE_MOCK_HMRC_SERVICE = env.bool("ENABLE_MOCK_HMRC_SERVICE", default=False)
if ENABLE_MOCK_HMRC_SERVICE:
    INSTALLED_APPS += ["mock_hmrc.apps.MockHmrcConfig"]

# Which system identifier to use in licence requests to HMRC's CHIEF system.
# LITE (and SPIRE) uses "SPIRE". ICMS uses "ILBDOTI".
CHIEF_SOURCE_SYSTEM = env("CHIEF_SOURCE_SYSTEM", default="SPIRE")

INCOMING_EMAIL_PASSWORD = env("INCOMING_EMAIL_PASSWORD", default="")
INCOMING_EMAIL_HOSTNAME = env("INCOMING_EMAIL_HOSTNAME", default="")
INCOMING_EMAIL_USER = env("INCOMING_EMAIL_USER", default="")
INCOMING_EMAIL_POP3_PORT = env("INCOMING_EMAIL_POP3_PORT", default=None)
INCOMING_EMAIL_CHECK_LIMIT = env.int("INCOMING_EMAIL_CHECK_LIMIT", default=100)

HMRC_TO_DIT_EMAIL_PASSWORD = env("HMRC_TO_DIT_EMAIL_PASSWORD", default="")
HMRC_TO_DIT_EMAIL_HOSTNAME = env("HMRC_TO_DIT_EMAIL_HOSTNAME", default="")
HMRC_TO_DIT_EMAIL_USER = env("HMRC_TO_DIT_EMAIL_USER", default="")
HMRC_TO_DIT_EMAIL_POP3_PORT = env("HMRC_TO_DIT_EMAIL_POP3_PORT", default="")

OUTGOING_EMAIL_USER = env("OUTGOING_EMAIL_USER")

MOCK_HMRC_EMAIL_PASSWORD = env("MOCK_HMRC_EMAIL_PASSWORD", default="")
MOCK_HMRC_EMAIL_HOSTNAME = env("MOCK_HMRC_EMAIL_HOSTNAME", default="")
MOCK_HMRC_EMAIL_USER = env("MOCK_HMRC_EMAIL_USER", default="")
MOCK_HMRC_EMAIL_POP3_PORT = env("MOCK_HMRC_EMAIL_POP3_PORT", default=None)

SPIRE_STANDIN_EMAIL_PASSWORD = env("SPIRE_STANDIN_EMAIL_PASSWORD", default="")
SPIRE_STANDIN_EMAIL_HOSTNAME = env("SPIRE_STANDIN_EMAIL_HOSTNAME", default="")
SPIRE_STANDIN_EMAIL_USER = env("SPIRE_STANDIN_EMAIL_USER", default="")
SPIRE_STANDIN_EMAIL_POP3_PORT = env("SPIRE_STANDIN_EMAIL_POP3_PORT", default=None)

SPIRE_INCOMING_EMAIL_ADDRESS = env("SPIRE_INCOMING_EMAIL_ADDRESS", default="spire-incoming@example.com")  # /PS-IGNORE
SPIRE_FROM_ADDRESS = env("SPIRE_FROM_ADDRESS", default="spire@example.com")  # /PS-IGNORE
HMRC_TO_DIT_REPLY_ADDRESS = env("HMRC_TO_DIT_REPLY_ADDRESS", default="hmrctodit@example.com")  # /PS-IGNORE

EMAIL_PASSWORD = env("EMAIL_PASSWORD")
EMAIL_HOSTNAME = env("EMAIL_HOSTNAME")
EMAIL_USER = env("EMAIL_USER")
EMAIL_POP3_PORT = env("EMAIL_POP3_PORT")
EMAIL_SMTP_PORT = env("EMAIL_SMTP_PORT")
SPIRE_ADDRESS = env("SPIRE_ADDRESS", default="test-spire-address@example.com")  # /PS-IGNORE
HMRC_ADDRESS = env("HMRC_ADDRESS", default="test-hmrc-address@example.com")  # /PS-IGNORE
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
MAILHOG_URL = env.str("MAILHOG_URL", default="http://localhost:8025")

TIME_TESTS = env.bool("TIME_TESTS", default=False)

LOCK_INTERVAL = env.float("LOCK_INTERVAL", default=120.0)

INBOX_POLL_INTERVAL = env.int("INBOX_POLL_INTERVAL", default=600)
LITE_LICENCE_DATA_POLL_INTERVAL = env.int("LITE_LICENCE_DATA_POLL_INTERVAL", default=600)
EMAIL_AWAITING_REPLY_TIME = env.int("EMAIL_AWAITING_REPLY_TIME", default=3600)
EMAIL_AWAITING_CORRECTIONS_TIME = env.int("EMAIL_AWAITING_CORRECTIONS_TIME", default=3600)
NOTIFY_USERS = env.json("NOTIFY_USERS", default=[])
LICENSE_POLL_INTERVAL = env.int("LICENSE_POLL_INTERVAL", default=300)

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

SYSTEM_INSTANCE_UUID = uuid.uuid4()

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = env.bool("USE_TZ", default=True)

_log_level = env.str("LOG_LEVEL", default="INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = "/static/"

# HAWK
HAWK_AUTHENTICATION_ENABLED = env.bool("HAWK_AUTHENTICATION_ENABLED", default=True)
HAWK_RECEIVER_NONCE_EXPIRY_SECONDS = 60
HAWK_ALGORITHM = "sha256"
HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS = "hmrc-integration"
LITE_API_ID = "lite-api"

HAWK_CREDENTIALS = {
    HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS: {
        "id": HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS,
        "key": env("LITE_HMRC_INTEGRATION_HAWK_KEY"),
        "algorithm": HAWK_ALGORITHM,
    },
    LITE_API_ID: {
        "id": LITE_API_ID,
        "key": env("LITE_API_HAWK_KEY"),
        "algorithm": HAWK_ALGORITHM,
    },
}

# The URL for licence usage callbacks. If there is no path component, defaults
# to `/licences/hmrc-integration/`.
LITE_API_URL = env("LITE_API_URL")
LITE_API_REQUEST_TIMEOUT = 60  # Maximum time, in seconds, to wait between bytes of a response

# The URL used to send licence reply data to ICMS
ICMS_API_URL = env("ICMS_API_URL", default="http://web:8080/")

# Sentry
if env.str("SENTRY_DSN", ""):
    sentry_sdk.init(
        dsn=env.str("SENTRY_DSN"),
        environment=env.str("SENTRY_ENVIRONMENT"),
        integrations=[DjangoIntegration()],
        send_default_pii=True,
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", 1.0),
    )
    SENTRY_ENABLED = True
else:
    SENTRY_ENABLED = False


DEFAULT_ENCODING = "iso-8859-1"

AZURE_AUTH_CLIENT_ID = env.str("AZURE_AUTH_CLIENT_ID")
AZURE_AUTH_CLIENT_SECRET = env.str("AZURE_AUTH_CLIENT_SECRET")
AZURE_AUTH_TENANT_ID = env.str("AZURE_AUTH_TENANT_ID")

SEND_REJECTED_EMAIL = env.bool("SEND_REJECTED_EMAIL", default=True)

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", False)
CELERY_TASK_STORE_EAGER_RESULT = env.bool("CELERY_TASK_STORE_EAGER_RESULT", False)
CELERY_TASK_SEND_SENT_EVENT = env.bool("CELERY_TASK_SEND_SENT_EVENT", True)


S3_BUCKET_TAG_ANONYMISER_DESTINATION = "anonymiser"

AWS_ENDPOINT_URL = env("AWS_ENDPOINT_URL", default=None)

DB_ANONYMISER_CONFIG_LOCATION = Path(BASE_DIR) / "conf" / "anonymise_model_config.yaml"
DB_ANONYMISER_DUMP_FILE_NAME = env.str("DB_ANONYMISER_DUMP_FILE_NAME", "anonymised.sql")


def _build_redis_url(base_url, db_number, **query_args):
    encoded_query_args = urlencode(query_args)
    return f"{base_url}/{db_number}?{encoded_query_args}"


if IS_ENV_GOV_PAAS:
    # Database
    # https://docs.djangoproject.com/en/2.1/ref/settings/#databases
    DATABASES = {"default": env.db()}
    for bucket_details in VCAP_SERVICES["aws-s3-bucket"]:
        if S3_BUCKET_TAG_ANONYMISER_DESTINATION in bucket_details["tags"]:
            aws_credentials = bucket_details["credentials"]
            DB_ANONYMISER_AWS_ENDPOINT_URL = None
            DB_ANONYMISER_AWS_ACCESS_KEY_ID = aws_credentials["aws_access_key_id"]
            DB_ANONYMISER_AWS_SECRET_ACCESS_KEY = aws_credentials["aws_secret_access_key"]
            DB_ANONYMISER_AWS_REGION = aws_credentials["aws_region"]
            DB_ANONYMISER_AWS_STORAGE_BUCKET_NAME = aws_credentials["bucket_name"]
    REDIS_BASE_URL = VCAP_SERVICES["redis"][0]["credentials"]["uri"]
    # Application Performance Monitoring
    if env.str("ELASTIC_APM_SERVER_URL", ""):
        ELASTIC_APM = {
            "SERVICE_NAME": env.str("ELASTIC_APM_SERVICE_NAME", default="lite-hmrc"),
            "SECRET_TOKEN": env.str("ELASTIC_APM_SECRET_TOKEN"),
            "SERVER_URL": env.str("ELASTIC_APM_SERVER_URL"),
            "ENVIRONMENT": env.str("SENTRY_ENVIRONMENT"),
            "DEBUG": DEBUG,
        }
        INSTALLED_APPS.append("elasticapm.contrib.django")

        if REDIS_BASE_URL:
            # Give celery tasks their own redis DB - future uses of redis should use a different DB
            REDIS_CELERY_DB = env("REDIS_CELERY_DB", default=0)
            is_redis_ssl = REDIS_BASE_URL.startswith("rediss://")
            url_args = {"ssl_cert_reqs": "CERT_REQUIRED"} if is_redis_ssl else {}

            CELERY_BROKER_URL = _build_redis_url(REDIS_BASE_URL, REDIS_CELERY_DB, **url_args)
            CELERY_RESULT_BACKEND = CELERY_BROKER_URL

        CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.redis.RedisCache",
                "LOCATION": REDIS_BASE_URL,
            }
        }

        LOGGING.update({"formatters": {"ecs_formatter": {"()": ECSFormatter}}})
        LOGGING.update({"handlers": {"ecs": {"class": "logging.StreamHandler", "formatter": "ecs_formatter"}}})
        LOGGING.update({"root": {"handlers": ["ecs"], "level": _log_level.upper()}})

elif IS_ENV_DBT_PLATFORM:
    ALLOWED_HOSTS = setup_allowed_hosts(ALLOWED_HOSTS)
    DATABASES = {"default": dj_database_url.config(default=database_url_from_env("DATABASE_CREDENTIALS"))}
    # Application Performance Monitoring
    if env.str("OPENSEARCH_APM_SERVER_URL", ""):
        ELASTIC_APM = {
            "SERVICE_NAME": env.str("OPENSEARCH_APM_SERVICE_NAME", default="lite-hmrc"),
            "SECRET_TOKEN": env.str("OPENSEARCH_APM_SECRET_TOKEN"),
            "SERVER_URL": env.str("ELASTIC_APM_SERVER_URL"),
            "ENVIRONMENT": env.str("SENTRY_ENVIRONMENT"),
            "DEBUG": DEBUG,
        }

    REDIS_BASE_URL = env("REDIS_BASE_URL", default=None)
    REDIS_CELERY_DB = env("REDIS_CELERY_DB", default=0)

    if REDIS_BASE_URL:
        is_redis_ssl = REDIS_BASE_URL.startswith("rediss://")
        url_args = {"ssl_cert_reqs": "CERT_REQUIRED"} if is_redis_ssl else {}

        CELERY_BROKER_URL = _build_redis_url(REDIS_BASE_URL, REDIS_CELERY_DB, **url_args)
        CELERY_RESULT_BACKEND = CELERY_BROKER_URL

    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_BASE_URL,
        }
    }

    DB_ANONYMISER_AWS_ENDPOINT_URL = AWS_ENDPOINT_URL
    DB_ANONYMISER_AWS_ACCESS_KEY_ID = env("DB_ANONYMISER_AWS_ACCESS_KEY_ID", default=None)
    DB_ANONYMISER_AWS_SECRET_ACCESS_KEY = env("DB_ANONYMISER_AWS_SECRET_ACCESS_KEY", default=None)
    DB_ANONYMISER_AWS_REGION = env("DB_ANONYMISER_AWS_REGION", default=None)
    DB_ANONYMISER_AWS_STORAGE_BUCKET_NAME = env("DB_ANONYMISER_AWS_STORAGE_BUCKET_NAME", default=None)

    LOGGING.update({"formatters": {"asim_formatter": {"()": ASIMFormatter}}})
    LOGGING.update({"handlers": {"asim": {"class": "logging.StreamHandler", "formatter": "asim_formatter"}}})
    LOGGING.update({"root": {"handlers": ["asim"], "level": _log_level.upper()}})

else:
    # Database
    # https://docs.djangoproject.com/en/2.1/ref/settings/#databases
    DATABASES = {"default": env.db()}
    REDIS_BASE_URL = env("REDIS_BASE_URL", default=None)
    DB_ANONYMISER_AWS_ENDPOINT_URL = AWS_ENDPOINT_URL
    DB_ANONYMISER_AWS_ACCESS_KEY_ID = env("DB_ANONYMISER_AWS_ACCESS_KEY_ID", default=None)
    DB_ANONYMISER_AWS_SECRET_ACCESS_KEY = env("DB_ANONYMISER_AWS_SECRET_ACCESS_KEY", default=None)
    DB_ANONYMISER_AWS_REGION = env("DB_ANONYMISER_AWS_REGION", default=None)
    DB_ANONYMISER_AWS_STORAGE_BUCKET_NAME = env("DB_ANONYMISER_AWS_STORAGE_BUCKET_NAME", default=None)
    # Application Performance Monitoring
    if env.str("ELASTIC_APM_SERVER_URL", ""):
        ELASTIC_APM = {
            "SERVICE_NAME": env.str("ELASTIC_APM_SERVICE_NAME", default="lite-hmrc"),
            "SECRET_TOKEN": env.str("ELASTIC_APM_SECRET_TOKEN"),
            "SERVER_URL": env.str("ELASTIC_APM_SERVER_URL"),
            "ENVIRONMENT": env.str("SENTRY_ENVIRONMENT"),
            "DEBUG": DEBUG,
        }
        INSTALLED_APPS.append("elasticapm.contrib.django")

    if REDIS_BASE_URL:
        # Give celery tasks their own redis DB - future uses of redis should use a different DB
        REDIS_CELERY_DB = env("REDIS_CELERY_DB", default=0)
        is_redis_ssl = REDIS_BASE_URL.startswith("rediss://")
        url_args = {"ssl_cert_reqs": "CERT_REQUIRED"} if is_redis_ssl else {}

        CELERY_BROKER_URL = _build_redis_url(REDIS_BASE_URL, REDIS_CELERY_DB, **url_args)
        CELERY_RESULT_BACKEND = CELERY_BROKER_URL

        CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.redis.RedisCache",
                "LOCATION": REDIS_BASE_URL,
            }
        }

    if "test" in sys.argv:
        LOGGING.update({"disable_existing_loggers": True})

    else:
        LOGGING.update({"formatters": {"simple": {"format": "{asctime} {levelname} {message}", "style": "{"}}})
        LOGGING.update({"handlers": {"stdout": {"class": "logging.StreamHandler", "formatter": "simple"}}})
        LOGGING.update({"root": {"handlers": ["stdout"], "level": _log_level.upper()}})
