# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from press.api.public_update_schedule import (
	change_password,
	create_link,
	get_public_schedule,
	set_enabled,
	unlock,
)
from press.press.doctype.team.test_team import create_test_press_admin_team


class TestPublicUpdateSchedule(FrappeTestCase):
	def setUp(self):
		self.team = create_test_press_admin_team()
		frappe.set_user(self.team.user)

	def tearDown(self):
		frappe.db.rollback()
		frappe.set_user("Administrator")

	def test_password_change_invalidates_existing_access(self):
		link = create_link("Production Schedule")
		self.assertRegex(link["password"], r"^[0-9a-f]{32}$")
		access = unlock(link["token"], link["password"])

		change_password(link["name"], "Replacement123")

		self.assertRaises(
			frappe.AuthenticationError,
			get_public_schedule,
			link["token"],
			access["access_token"],
			"2026-07-01 00:00:00",
			"2026-08-01 00:00:00",
		)
		self.assertTrue(unlock(link["token"], "Replacement123")["access_token"])

	def test_disabled_link_cannot_be_unlocked(self):
		link = create_link("Production Schedule")

		set_enabled(link["name"], 0)

		self.assertRaises(
			frappe.AuthenticationError,
			unlock,
			link["token"],
			link["password"],
		)

	def test_public_schedule_rejects_oversized_range(self):
		link = create_link("Production Schedule")
		access = unlock(link["token"], link["password"])

		self.assertRaises(
			frappe.ValidationError,
			get_public_schedule,
			link["token"],
			access["access_token"],
			"2026-01-01 00:00:00",
			"2026-04-01 00:00:00",
		)

	@patch("press.api.public_update_schedule.get_updates")
	def test_public_response_contains_read_only_schedule_fields(self, get_updates):
		link = create_link("Production Schedule")
		access = unlock(link["token"], link["password"])
		get_updates.return_value = [
			frappe._dict(
				name="update-1",
				site="alpha.example.com",
				status="Scheduled",
				scheduled_time="2026-07-30 03:00:00",
				update_start=None,
				update_end=None,
				update_duration=None,
				event_time="2026-07-30 03:00:00",
				skipped_backups=1,
			)
		]

		result = get_public_schedule(
			link["token"],
			access["access_token"],
			"2026-07-01 00:00:00",
			"2026-08-01 00:00:00",
		)

		self.assertEqual(result["title"], "Production Schedule")
		self.assertEqual(
			set(result["updates"][0]),
			{
				"site",
				"status",
				"scheduled_time",
				"update_start",
				"update_end",
				"update_duration",
				"event_time",
			},
		)
		get_updates.assert_called_once_with(
			frappe.utils.get_datetime("2026-07-01 00:00:00"),
			frappe.utils.get_datetime("2026-08-01 00:00:00"),
			self.team.name,
		)
