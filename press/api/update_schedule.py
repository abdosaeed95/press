# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder.functions import Coalesce
from frappe.utils import get_datetime

from press.press.doctype.site_update.site_update import benches_with_available_update
from press.utils import get_current_team


@frappe.whitelist()
def get(start: str, end: str):
	start = get_datetime(start)
	end = get_datetime(end)
	if end <= start:
		frappe.throw(frappe._("Schedule end must be after schedule start."))

	return {
		"updates": get_updates(start, end),
		"pending_sites": get_pending_sites(),
	}


def get_updates(start, end):
	site_update = frappe.qb.DocType("Site Update")
	event_time = Coalesce(
		site_update.scheduled_time,
		site_update.update_end,
		site_update.update_start,
		site_update.creation,
	)

	return (
		frappe.qb.from_(site_update)
		.select(
			site_update.name,
			site_update.site,
			site_update.status,
			site_update.scheduled_time,
			site_update.update_start,
			site_update.update_end,
			site_update.update_duration,
			site_update.skipped_backups,
			site_update.skipped_failing_patches,
			event_time.as_("event_time"),
		)
		.where(site_update.team == get_current_team())
		.where(event_time >= start)
		.where(event_time < end)
		.orderby(event_time)
	).run(as_dict=True)


def get_pending_sites():
	benches = benches_with_available_update()
	if not benches:
		return []

	site = frappe.qb.DocType("Site")
	site_update = frappe.qb.DocType("Site Update")
	active_update_sites = (
		frappe.qb.from_(site_update)
		.select(site_update.site)
		.where(site_update.status.isin(["Scheduled", "Pending", "Running", "Recovering"]))
	)

	return (
		frappe.qb.from_(site)
		.select(site.name, site.host_name, site.status, site.bench)
		.where(site.team == get_current_team())
		.where(site.status.isin(["Active", "Inactive", "Suspended", "Broken"]))
		.where(site.bench.isin(benches))
		.where(site.name.notin(active_update_sites))
		.orderby(site.host_name)
	).run(as_dict=True)
