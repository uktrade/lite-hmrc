import unittest
from unittest import mock

from mail.libraries.helpers import log_to_sentry


class TestLogToSentry(unittest.TestCase):

    @mock.patch("sentry_sdk.capture_message")
    def test_log_to_sentry(self, mock_capture_message):
        log_to_sentry("some message", {"extra": "context"}, level="debug")
        mock_capture_message.assert_called_with("some message", level="debug")
