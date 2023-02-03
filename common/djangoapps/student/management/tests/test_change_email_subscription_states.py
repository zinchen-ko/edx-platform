"""Tests for change email subscription states management command"""

from tempfile import NamedTemporaryFile
from unittest.mock import patch

import pytest
import six
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

COMMAND = 'change_email_subscription_states'


class ChangeEmailSubscriptionTests(TestCase):
    """
    Tests change_email_subscription_states command
    """

    def setUp(self):
        """
        Set up tests
        """
        super().setUp()
        self.unsubscribed_state = 'unsubscribed'
        self.lines = [
            f"test_user{i}@test.com" for i in range(10)
        ]

    @staticmethod
    def _write_test_csv(csv, lines):
        """Write a test csv file with the lines provided"""
        csv.write(b"email\n")
        for line in lines:
            csv.write(six.b(line))
        csv.seek(0)
        return csv

    @patch("common.djangoapps.student.management.commands.change_email_subscription_states.get_braze_client")
    def test_change_email_subscription_state(self, mock_get_braze_client):
        """ Test CSV file with subscription state"""

        with NamedTemporaryFile() as csv:
            csv = self._write_test_csv(csv, self.lines)

            call_command(
                COMMAND,
                '--csv_path',
                csv.name,
                '--subscription_state',
                self.unsubscribed_state
            )

        mock_get_braze_client.assert_called_once()

    def test_command_error_for_csv_path(self):
        """ Test command error raised if csv_path is not valid"""

        with pytest.raises(CommandError):
            call_command(
                COMMAND,
                '--csv_path',
                '/test/test.csv',
                '--subscription_state',
                self.unsubscribed_state
            )

    def test_command_error_for_subscription_state(self):
        """ Test command error raised if subscription state is not valid"""

        with NamedTemporaryFile() as csv:
            csv = self._write_test_csv(csv, self.lines)

            with pytest.raises(CommandError):
                call_command(
                    COMMAND,
                    '--csv_path',
                    csv.name,
                    '--subscription_state',
                    'test'
                )
