# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

from unittest import TestCase
from unittest.mock import MagicMock, patch

from press.press.doctype.console_integration_settings.console_integration_settings import (
	ConsoleIntegrationSettings,
)


class TestConsoleIntegrationSettings(TestCase):
	@patch(
		"press.press.doctype.console_integration_settings.console_integration_settings.FrappeClient"
	)
	def test_only_setup_active_slaves_are_linked(self, frappe_client):
		client = frappe_client.return_value.__enter__.return_value
		client.get_list.side_effect = [
			[{"name": "master.example.com", "subscription": "SUB-1"}],
			[{"subscription": "SUB-1"}],
		]
		settings = MagicMock(
			console_url="https://console.example.com",
			username="user@example.com",
		)
		settings.get_password.return_value = "password"

		self.assertEqual(
			ConsoleIntegrationSettings.get_sites_without_slaves(
				settings, ["master.example.com", "without-slave.example.com"]
			),
			["without-slave.example.com"],
		)
		self.assertEqual(
			client.get_list.call_args_list[1].kwargs["filters"],
			{
				"subscription": ["in", ["SUB-1"]],
				"instance_type": "Slave",
				"setup_complete": 1,
				"status": ["not in", ["Archived", "Archiving"]],
			},
		)
