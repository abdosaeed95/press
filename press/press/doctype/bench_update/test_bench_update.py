# Copyright (c) 2023, Frappe and Contributors
# See license.txt

from types import SimpleNamespace
from unittest.mock import Mock, patch

from frappe.tests.utils import FrappeTestCase

from press.press.doctype.bench_update.bench_update import BenchUpdate


class TestBenchUpdate(FrappeTestCase):
	@patch("press.press.doctype.bench_update.bench_update.frappe.db.set_value")
	def test_scheduled_updates_are_reserved_until_the_new_bench_is_ready(self, set_value):
		bench_update = SimpleNamespace(
			name="bench-update-1",
			sites=[
				SimpleNamespace(site_update="site-update-1"),
				SimpleNamespace(site_update=None),
			],
		)

		BenchUpdate.reserve_scheduled_site_updates(bench_update)

		set_value.assert_called_once_with(
			"Site Update",
			{"name": ("in", ["site-update-1"]), "status": "Scheduled"},
			"pending_bench_update",
			"bench-update-1",
		)

	@patch("press.press.doctype.bench_update.bench_update.frappe.db.commit")
	@patch("press.press.doctype.bench_update.bench_update.frappe.get_doc")
	@patch("press.press.doctype.bench_update.bench_update.frappe.get_value")
	def test_existing_scheduled_update_is_retargeted(
		self,
		get_value,
		get_doc,
		commit,
	):
		get_value.side_effect = ["Active", "source-bench", "source-candidate"]
		site_update = Mock()
		get_doc.return_value = site_update
		row = SimpleNamespace(
			name="bench-site-update",
			site="test.example.com",
			server="server-1",
			source_candidate="source-candidate",
			status="Scheduled",
			site_update="site-update-1",
		)
		bench_update = SimpleNamespace(sites=[row], add_comment=Mock())
		bench_update.schedule_site_update = BenchUpdate.schedule_site_update.__get__(bench_update)

		BenchUpdate.update_sites_on_server(bench_update, "destination-bench", "server-1")

		get_doc.assert_called_once_with("Site Update", "site-update-1")
		site_update.retarget.assert_called_once_with("destination-bench")
		commit.assert_called_once()
