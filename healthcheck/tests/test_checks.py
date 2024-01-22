import logging
import unittest
import pytest
from unittest.mock import Mock
from healthcheck.exceptions import HealthCheckException
from healthcheck.checks import celery_health_check, add
from celery.exceptions import TaskRevokedError, TimeoutError


@pytest.fixture
def mock_settings():
    return {
        "HEALTHCHECK_CELERY_TIMEOUT": 3,
        "HEALTHCHECK_CELERY_RESULT_TIMEOUT": 3,
        "HEALTHCHECK_CELERY_QUEUE_TIMEOUT": 3,
    }


@pytest.fixture
def mock_logger():
    logger = logging.getLogger("health-check")
    logger.error = Mock()
    logger.exception = Mock()
    return logger


@pytest.fixture
def add_mock():
    return Mock()


def test_add_task():
    result = add(4, 5)
    assert result == 9


def test_celery_health_check_successful(mock_settings, mock_logger, add_mock):
    add_mock.apply_async.return_value.result = 8

    with unittest.mock.patch("healthcheck.checks.add", add_mock), unittest.mock.patch(
        "django.conf.settings", mock_settings
    ):
        result = celery_health_check()

    assert result is True


def test_celery_health_check_unexpected_result(mock_settings, mock_logger, add_mock):
    add_mock.apply_async.return_value.result = 10

    with unittest.mock.patch("healthcheck.checks.add", add_mock), unittest.mock.patch(
        "django.conf.settings", mock_settings
    ):
        result = celery_health_check()

    assert result is False


def test_celery_health_check_health_check_exception(mock_settings, mock_logger, add_mock):
    add_mock.apply_async.side_effect = HealthCheckException("Health check failed")

    with unittest.mock.patch("healthcheck.checks.add", add_mock), unittest.mock.patch(
        "django.conf.settings", mock_settings
    ):
        result = celery_health_check()

    assert result is False


@pytest.mark.parametrize("exception", [IOError, NotImplementedError, TaskRevokedError, TimeoutError])
def test_celery_health_check_exceptions(exception, mock_settings, mock_logger, add_mock):
    add_mock.apply_async.side_effect = exception

    with unittest.mock.patch("healthcheck.checks.add", add_mock), unittest.mock.patch(
        "django.conf.settings", mock_settings
    ):
        result = celery_health_check()

    assert result is False


def test_celery_health_check_base_exception(mock_settings, mock_logger, add_mock):
    add_mock.apply_async.side_effect = BaseException("Unexpecter Error!")

    with unittest.mock.patch("healthcheck.checks.add", add_mock), unittest.mock.patch(
        "django.conf.settings", mock_settings
    ):
        result = celery_health_check()

    assert result is False
