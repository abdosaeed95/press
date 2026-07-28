# Copyright (c) 2023, Frappe and contributors
# For license information, please see license.txt

import frappe

from press.api.server import prometheus_query
from press.utils import CAIRO_TIMEZONE


def execute(filters=None):
	columns = [
		{
			"fieldname": "bench",
			"label": frappe._("Bench"),
			"fieldtype": "Link",
			"options": "Bench",
			"width": 200,
		},
		{
			"fieldname": "workload",
			"label": frappe._("Workload"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "allocated_ram",
			"label": frappe._("Allocated RAM (based on current workers)"),
			"fieldtype": "Float",
			"width": 200,
		},
		{
			"fieldname": "5m_avg_server_ram",
			"label": frappe._("5m average RAM"),
			"fieldtype": "Float",
			"width": 200,
		},
		{
			"fieldname": "6h_avg_server_ram",
			"label": frappe._("6h average RAM"),
			"fieldtype": "Float",
			"width": 200,
		},
		{
			"fieldname": "max_server_ram",
			"label": frappe._("6h max RAM"),
			"fieldtype": "Float",
			"width": 200,
		},
	]

	return columns, get_data(filters)


def get_data(filters):
	server_name = filters.get("server")
	benches = frappe.get_all(
		"Bench",
		filters={
			"server": server_name,
			"status": "Active",
			"auto_scale_workers": True,
		},
		pluck="name",
	)
	server = frappe.get_doc("Server", server_name)
	result = []
	for bench_name in benches:
		bench = frappe.get_doc("Bench", bench_name)

		gn, bg = bench.allocate_workers(server.workload, server.max_gunicorn_workers, server.max_bg_workers)
		result.append(
			{
				"bench": bench_name,
				"workload": bench.workload,
				"allocated_ram": gn * 150 + bg * (3 * 80),
			}
		)

	for fieldname, query, timespan in (
		(
			"5m_avg_server_ram",
			f'sum(avg_over_time(container_memory_rss{{instance="{server_name}", name=~".+"}}[5m])) by (name)',
			60,
		),
		(
			"6h_avg_server_ram",
			f'sum(avg_over_time(container_memory_rss{{instance="{server_name}", name=~".+"}}[6h])) by (name)',
			6 * 3600,
		),
		(
			"max_server_ram",
			f'sum(max_over_time(container_memory_rss{{instance="{server_name}", name=~".+"}}[6h])) by (name)',
			6 * 3600,
		),
	):
		set_memory_usage(result, server_name, fieldname, query, timespan)

	return result


def set_memory_usage(result, server_name, fieldname, query, timespan):
	memory_by_bench = {
		row["name"]["name"]: row["values"][-1] / 1024 / 1024
		for row in prometheus_query(query, lambda x: x, CAIRO_TIMEZONE, timespan, 60)["datasets"]
	}
	for row in result:
		if row["bench"] in memory_by_bench:
			row[fieldname] = memory_by_bench[row["bench"]]
