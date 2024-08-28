import unittest
from unittest import mock

from mail.libraries.helpers import log_to_sentry


class TestLogToSentry(unittest.TestCase):

    @mock.patch("sentry_sdk.scope.Scope.capture_event")
    def test_log_to_sentry(self, mock_capture_event):
        log_to_sentry("some message", {"extra": "context"}, level="debug")
        mock_capture_event.assert_called_with(
            {"message": "some message", "level": "debug"},
            scope=None,
        )
