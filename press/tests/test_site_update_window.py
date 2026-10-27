import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from croniter import croniter

from press import hooks
from press.press.doctype.site_update import scheduled_auto_updates, site_update


class TestSiteUpdateWindow(unittest.TestCase):
	def test_cairo_boundaries_and_daylight_saving(self):
		for month in (1, 7):
			for hour, minute, second, expected in (
				(3, 59, 59, False),
				(4, 0, 0, True),
				(6, 59, 59, True),
				(7, 0, 0, False),
				(23, 0, 0, False),
			):
				local = datetime(2026, month, 15, hour, minute, second, tzinfo=ZoneInfo("Africa/Cairo"))
				utc = local.astimezone(timezone.utc)
				clock = Mock(side_effect=lambda zone, current=utc: current.astimezone(ZoneInfo(zone)))
				fake = SimpleNamespace(
					utils=SimpleNamespace(get_datetime_in_timezone=clock),
					get_hooks=Mock(return_value=hooks.deploy_hours),
				)
				with self.subTest(month=month, time=local), patch.object(site_update, "frappe", fake):
					self.assertEqual(site_update.is_site_in_deploy_hours(), expected)
					clock.assert_called_once_with("Africa/Cairo")

	def test_all_weekdays_match_the_cairo_window_and_cron(self):
		for start in (datetime(2026, 1, 11, 5), datetime(2026, 7, 12, 5)):
			for offset in range(7):
				local = (start + timedelta(days=offset)).replace(tzinfo=ZoneInfo("Africa/Cairo"))
				expected = offset < 5  # The sequence starts on Sunday.
				utc = local.astimezone(timezone.utc)
				fake = SimpleNamespace(
					utils=SimpleNamespace(
						get_datetime_in_timezone=lambda zone, current=utc: current.astimezone(ZoneInfo(zone))
					),
					get_hooks=Mock(return_value=hooks.deploy_hours),
				)
				with self.subTest(time=local), patch.object(site_update, "frappe", fake):
					for status in ("Active", "Inactive", "Suspended"):
						site = SimpleNamespace(status=status, timezone="Asia/Tokyo")
						self.assertEqual(site_update.is_site_in_deploy_hours(site), expected)
					for interval in (15, 30):
						self.assertEqual(croniter.match(f"*/{interval} 4-6 * * 0-4", local), expected)

	def test_automatic_entrypoints_do_not_start_updates_on_weekends(self):
		for day in (16, 17):  # Friday and Saturday.
			fake = Mock()
			fake.utils.get_datetime_in_timezone.return_value = datetime(
				2026, 1, day, 5, tzinfo=ZoneInfo("Africa/Cairo")
			)
			fake.get_hooks.return_value = hooks.deploy_hours
			with (
				self.subTest(day=day),
				patch.object(site_update, "frappe", fake),
				patch.object(scheduled_auto_updates, "frappe", fake),
			):
				site_update.schedule_updates()
				site_update.schedule_updates_server("server")
				scheduled_auto_updates.trigger()
			fake.get_all.assert_not_called()
			fake.get_doc.assert_not_called()
			fake.enqueue.assert_not_called()
			self.assertEqual(fake.db.mock_calls, [])

	def test_cron_waits_until_sunday_after_thursday_window(self):
		for interval in (15, 30):
			schedule = croniter(f"*/{interval} 4-6 * * 0-4", datetime(2026, 1, 15, 6, 59, 59))
			self.assertEqual(schedule.get_next(datetime), datetime(2026, 1, 18, 4))

	def test_inactive_and_other_timezones_cannot_bypass_cairo_window(self):
		fake = SimpleNamespace(
			utils=SimpleNamespace(
				get_datetime_in_timezone=Mock(
					return_value=datetime(2026, 1, 15, 12, tzinfo=ZoneInfo("Africa/Cairo"))
				)
			),
			get_hooks=Mock(return_value=hooks.deploy_hours),
		)
		with patch.object(site_update, "frappe", fake):
			for status in ("Active", "Inactive", "Suspended"):
				self.assertFalse(
					site_update.is_site_in_deploy_hours(SimpleNamespace(status=status, timezone="Asia/Tokyo"))
				)

	def test_automatic_entrypoints_do_nothing_outside_window(self):
		for module, method, args in (
			(site_update, "schedule_updates", ()),
			(site_update, "schedule_updates_server", ("server",)),
			(scheduled_auto_updates, "trigger", ()),
		):
			fake = Mock()
			with (
				self.subTest(method=method),
				patch.object(module, "frappe", fake),
				patch.object(module, "is_site_in_deploy_hours", return_value=False),
			):
				getattr(module, method)(*args)
				self.assertEqual(fake.mock_calls, [])

	def test_dispatch_preserves_native_queue_inside_window(self):
		fake = SimpleNamespace(get_all=Mock(return_value=["server"]), enqueue=Mock())
		with (
			patch.object(site_update, "frappe", fake),
			patch.object(site_update, "is_site_in_deploy_hours", return_value=True),
		):
			site_update.schedule_updates()
		fake.enqueue.assert_called_once_with(
			"press.press.doctype.site_update.site_update.schedule_updates_server",
			server="server",
			job_id="schedule_updates:server",
			deduplicate=True,
			queue="long",
		)

	def test_worker_stops_before_next_site_when_window_closes(self):
		fake = SimpleNamespace(
			db=SimpleNamespace(get_single_value=Mock(return_value=10), count=Mock(return_value=0)),
			utils=SimpleNamespace(add_to_date=Mock(return_value="2026-01-15 00:00:00")),
			get_doc=Mock(),
		)
		with (
			patch.object(site_update, "frappe", fake),
			patch.object(site_update, "is_site_in_deploy_hours", side_effect=[True, True, False]),
			patch.object(
				site_update, "sites_with_available_update", return_value=[SimpleNamespace(bench="bench")]
			),
		):
			site_update.schedule_updates_server("server")
		fake.get_doc.assert_not_called()

	def test_configured_auto_schedule_stops_at_window_end(self):
		fake = SimpleNamespace(get_all=Mock(return_value=[SimpleNamespace(name="site")]), get_doc=Mock())
		with (
			patch.object(scheduled_auto_updates, "frappe", fake),
			patch.object(scheduled_auto_updates, "is_site_in_deploy_hours", side_effect=[True, False]),
			patch.object(scheduled_auto_updates, "benches_with_available_update", return_value=["bench"]),
			patch.object(scheduled_auto_updates, "should_update_trigger", return_value=True),
		):
			scheduled_auto_updates.trigger()
		fake.get_doc.assert_not_called()

	def test_only_automatic_cron_jobs_move_to_morning_window(self):
		cron = hooks.scheduler_events["cron"]
		methods = {
			"press.press.doctype.site_update.site_update.schedule_updates": "*/15 4-6 * * 0-4",
			"press.press.doctype.site_update.scheduled_auto_updates.trigger": "*/30 4-6 * * 0-4",
			"press.press.doctype.site_update.site_update.run_scheduled_updates": "*/15 * * * *",
			"press.press.doctype.site.backups.schedule_logical_backups": "*/15 * * * *",
			"press.press.doctype.site.backups.schedule_physical_backups": "*/15 * * * *",
		}
		for method, expected in methods.items():
			self.assertEqual([schedule for schedule, jobs in cron.items() if method in jobs], [expected])


if __name__ == "__main__":
	unittest.main()
