# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

from unittest.mock import Mock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from press.api.update_schedule import get
from press.press.doctype.site.test_site import create_test_site
from press.press.doctype.site_update.site_update import SiteUpdate
from press.press.doctype.team.test_team import create_test_press_admin_team, create_test_team


class TestUpdateSchedule(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()
		frappe.set_user("Administrator")

	@patch("press.api.update_schedule.benches_with_available_update")
	@patch.object(SiteUpdate, "validate", new=Mock())
	def test_schedule_is_team_scoped_and_excludes_scheduled_sites(self, available_benches):
		team = create_test_press_admin_team()
		other_team = create_test_team()
		frappe.set_user(team.user)

		scheduled_site = create_test_site(team=team.name)
		pending_site = create_test_site(bench=scheduled_site.bench, team=team.name)
		active_site = create_test_site(bench=scheduled_site.bench, team=team.name)
		other_site = create_test_site(bench=scheduled_site.bench, team=other_team.name)
		available_benches.return_value = [scheduled_site.bench]

		scheduled_time = frappe.utils.add_days(frappe.utils.now_datetime(), 2)
		frappe.get_doc(
			{
				"doctype": "Site Update",
				"site": scheduled_site.name,
				"team": team.name,
				"status": "Scheduled",
				"scheduled_time": scheduled_time,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Site Update",
				"site": active_site.name,
				"team": team.name,
				"status": "Pending",
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Site Update",
				"site": other_site.name,
				"team": other_team.name,
				"status": "Scheduled",
				"scheduled_time": scheduled_time,
			}
		).insert(ignore_permissions=True)

		schedule = get("2000-01-01 00:00:00", "2100-01-01 00:00:00")
		updates = {update.site: update for update in schedule["updates"]}

		self.assertEqual(set(updates), {scheduled_site.name, active_site.name})
		self.assertEqual(updates[scheduled_site.name].event_time, scheduled_time)
		self.assertEqual([site.name for site in schedule["pending_sites"]], [pending_site.name])

	def test_schedule_rejects_invalid_range(self):
		self.assertRaises(
			frappe.ValidationError,
			get,
			"2026-07-30 00:00:00",
			"2026-07-29 00:00:00",
		)
