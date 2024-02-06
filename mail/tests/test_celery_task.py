from unittest import mock

import pytest
from django.test import TestCase

from mail.celery_tasks import manage_inbox


class ManageInboxTests(TestCase):
    @mock.patch("mail.celery_tasks.check_and_route_emails")
    def test_manage_inbox(self, mock_function):
        manage_inbox()
        mock_function.assert_called_once()

    @mock.patch("mail.celery_tasks.check_and_route_emails")
    def test_error_manage_inbox(self, mock_function):
        mock_function.side_effect = Exception("Test Error")
        with pytest.raises(Exception) as excinfo:
            manage_inbox()
        assert str(excinfo.value) == "Test Error"
