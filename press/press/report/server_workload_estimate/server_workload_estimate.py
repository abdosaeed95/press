# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

SITE_DENSITY_PER_VCPU = 20
DATABASE_DENSITY_PER_VCPU = 50


def execute(filters=None):
	frappe.only_for(["System Manager", "Press Admin"])
	data = [build_workload(row) for row in get_data(frappe._dict(filters or {}))]
	return get_columns(), data, get_message(), None, get_summary(data)


def get_columns():
	return [
		{"fieldname": "server", "label": _("Server"), "fieldtype": "Link", "options": "Server"},
		{"fieldname": "status", "label": _("Status"), "fieldtype": "Data"},
		{"fieldname": "plan", "label": _("Server Plan"), "fieldtype": "Link", "options": "Server Plan"},
		{"fieldname": "vcpu", "label": _("vCPU"), "fieldtype": "Int"},
		{"fieldname": "memory_gb", "label": _("RAM (GB)"), "fieldtype": "Float", "precision": 1},
		{"fieldname": "disk_gb", "label": _("Disk (GB)"), "fieldtype": "Float", "precision": 1},
		{"fieldname": "total_sites", "label": _("Sites"), "fieldtype": "Int"},
		{"fieldname": "workload_sites", "label": _("Workload Sites"), "fieldtype": "Int"},
		{"fieldname": "inactive_sites", "label": _("Inactive Sites"), "fieldtype": "Int"},
		{"fieldname": "active_benches", "label": _("Active Benches"), "fieldtype": "Int"},
		{
			"fieldname": "cpu_hours_per_day",
			"label": _("Allocated CPU Hours / Day"),
			"fieldtype": "Float",
			"precision": 1,
		},
		{
			"fieldname": "cpu_commitment_percent",
			"label": _("CPU Commitment (%)"),
			"fieldtype": "Percent",
			"precision": 1,
		},
		{
			"fieldname": "allocated_memory_gb",
			"label": _("Allocated RAM (GB)"),
			"fieldtype": "Float",
			"precision": 1,
		},
		{
			"fieldname": "memory_commitment_percent",
			"label": _("RAM Commitment (%)"),
			"fieldtype": "Percent",
			"precision": 1,
		},
		{
			"fieldname": "site_storage_gb",
			"label": _("Site Storage (GB)"),
			"fieldtype": "Float",
			"precision": 1,
		},
		{
			"fieldname": "storage_commitment_percent",
			"label": _("Storage Commitment (%)"),
			"fieldtype": "Percent",
			"precision": 1,
		},
		{
			"fieldname": "database_server",
			"label": _("Database Server"),
			"fieldtype": "Link",
			"options": "Database Server",
		},
		{"fieldname": "database_count", "label": _("Databases"), "fieldtype": "Int"},
		{
			"fieldname": "database_size_gb",
			"label": _("Database Size (GB)"),
			"fieldtype": "Float",
			"precision": 1,
		},
		{
			"fieldname": "database_disk_gb",
			"label": _("Database Disk (GB)"),
			"fieldtype": "Float",
			"precision": 1,
		},
		{
			"fieldname": "database_commitment_percent",
			"label": _("Database Commitment (%)"),
			"fieldtype": "Percent",
			"precision": 1,
		},
		{
			"fieldname": "workload_score",
			"label": _("Estimated Load (%)"),
			"fieldtype": "Percent",
			"precision": 1,
		},
		{"fieldname": "workload_level", "label": _("Estimated Load Level"), "fieldtype": "Data"},
		{"fieldname": "usage_updated_on", "label": _("Usage Updated On"), "fieldtype": "Datetime"},
	]


def get_data(filters):
	conditions = []
	values = {}
	for fieldname in ("status", "server", "cluster", "team"):
		if filters.get(fieldname):
			conditions.append(f"server.`{fieldname if fieldname != 'server' else 'name'}` = %({fieldname})s")
			values[fieldname] = filters.get(fieldname)

	where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
	return frappe.db.sql(
		f"""
		WITH latest_usage AS (
			SELECT
				site_usage.*,
				ROW_NUMBER() OVER (
					PARTITION BY site_usage.site ORDER BY site_usage.creation DESC
				) AS usage_rank
			FROM `tabSite Usage` site_usage
		),
		site_stats AS (
			SELECT
				site.server,
				COUNT(*) AS total_sites,
				SUM(site.status IN ('Active', 'Pending', 'Updating')) AS workload_sites,
				SUM(site.status NOT IN ('Active', 'Pending', 'Updating')) AS inactive_sites,
				SUM(
					IF(site.status IN ('Active', 'Pending', 'Updating'), COALESCE(plan.cpu_time_per_day, 0), 0)
				) AS cpu_hours_per_day,
				SUM(COALESCE(latest.public, 0) + COALESCE(latest.private, 0) + COALESCE(latest.backups, 0)) / 1024 AS site_storage_gb,
				MAX(latest.creation) AS usage_updated_on
			FROM tabSite site
			LEFT JOIN `tabSite Plan` plan ON plan.name = site.plan
			LEFT JOIN latest_usage latest ON latest.site = site.name AND latest.usage_rank = 1
			WHERE site.status != 'Archived'
			GROUP BY site.server
		),
		bench_stats AS (
			SELECT
				bench.server,
				COUNT(*) AS active_benches,
				SUM(COALESCE(bench.memory_high, 0)) AS allocated_memory_mb
			FROM tabBench bench
			WHERE bench.status = 'Active'
			GROUP BY bench.server
		),
		database_stats AS (
			SELECT
				server.database_server,
				COUNT(*) AS database_count,
				SUM(COALESCE(latest.database, 0)) / 1024 AS database_size_gb,
				MAX(latest.creation) AS database_usage_updated_on
			FROM tabSite site
			JOIN tabServer server ON server.name = site.server
			LEFT JOIN latest_usage latest ON latest.site = site.name AND latest.usage_rank = 1
			WHERE site.status != 'Archived' AND server.database_server IS NOT NULL
			GROUP BY server.database_server
		)
		SELECT
			server.name AS server,
			server.status,
			server.plan,
			server.database_server,
			COALESCE(NULLIF(server_plan.vcpu, 0), NULLIF(server_vm.vcpu, 0), 0) AS vcpu,
			COALESCE(NULLIF(server.ram, 0), NULLIF(server_plan.memory, 0), NULLIF(server_vm.ram, 0), 0) AS memory_mb,
			COALESCE(NULLIF(server_vm.disk_size, 0), NULLIF(server_plan.disk, 0), 0) AS disk_gb,
			COALESCE(site_stats.total_sites, 0) AS total_sites,
			COALESCE(site_stats.workload_sites, 0) AS workload_sites,
			COALESCE(site_stats.inactive_sites, 0) AS inactive_sites,
			COALESCE(site_stats.cpu_hours_per_day, 0) AS cpu_hours_per_day,
			COALESCE(site_stats.site_storage_gb, 0) AS site_storage_gb,
			COALESCE(bench_stats.active_benches, 0) AS active_benches,
			COALESCE(bench_stats.allocated_memory_mb, 0) AS allocated_memory_mb,
			COALESCE(database_stats.database_count, 0) AS database_count,
			COALESCE(database_stats.database_size_gb, 0) AS database_size_gb,
			COALESCE(NULLIF(database_vm.vcpu, 0), NULLIF(database_plan.vcpu, 0), 0) AS database_vcpu,
			COALESCE(NULLIF(database_vm.disk_size, 0), NULLIF(database_plan.disk, 0), 0) AS database_disk_gb,
			CASE
				WHEN site_stats.usage_updated_on IS NULL THEN database_stats.database_usage_updated_on
				WHEN database_stats.database_usage_updated_on IS NULL THEN site_stats.usage_updated_on
				ELSE GREATEST(site_stats.usage_updated_on, database_stats.database_usage_updated_on)
			END AS usage_updated_on
		FROM tabServer server
		LEFT JOIN `tabServer Plan` server_plan ON server_plan.name = server.plan
		LEFT JOIN `tabVirtual Machine` server_vm ON server_vm.name = server.virtual_machine
		LEFT JOIN site_stats ON site_stats.server = server.name
		LEFT JOIN bench_stats ON bench_stats.server = server.name
		LEFT JOIN database_stats ON database_stats.database_server = server.database_server
		LEFT JOIN `tabDatabase Server` database_server ON database_server.name = server.database_server
		LEFT JOIN `tabServer Plan` database_plan ON database_plan.name = database_server.plan
		LEFT JOIN `tabVirtual Machine` database_vm ON database_vm.name = database_server.virtual_machine
		{where}
		ORDER BY server.name
		""",
		values=values,
		as_dict=True,
	)


def build_workload(row):
	row.memory_gb = flt(row.memory_mb) / 1024
	row.allocated_memory_gb = flt(row.allocated_memory_mb) / 1024
	row.cpu_commitment_percent = get_percent(row.cpu_hours_per_day, flt(row.vcpu) * 24)
	row.memory_commitment_percent = get_percent(row.allocated_memory_mb, row.memory_mb)
	row.storage_commitment_percent = get_percent(row.site_storage_gb, row.disk_gb)
	row.site_density_percent = get_percent(row.workload_sites, flt(row.vcpu) * SITE_DENSITY_PER_VCPU)
	row.database_commitment_percent = get_percent(row.database_size_gb, row.database_disk_gb)
	row.database_density_percent = get_percent(
		row.database_count, flt(row.database_vcpu) * DATABASE_DENSITY_PER_VCPU
	)

	application_score = get_weighted_score(
		(
			(row.cpu_commitment_percent, 40),
			(row.memory_commitment_percent, 30),
			(row.storage_commitment_percent, 20),
			(row.site_density_percent, 10),
		)
	)
	database_score = get_weighted_score(
		((row.database_commitment_percent, 75), (row.database_density_percent, 25))
	)
	scores = [score for score in (application_score, database_score) if score is not None]
	row.workload_score = max(scores) if scores else None
	row.workload_level = get_workload_level(row.workload_score)
	return row


def get_percent(value, capacity):
	return round(flt(value) / flt(capacity) * 100, 1) if flt(capacity) else None


def get_weighted_score(metrics):
	available = [(value, weight) for value, weight in metrics if value is not None]
	if not available:
		return None
	return round(
		sum(value * weight for value, weight in available) / sum(weight for _, weight in available), 1
	)


def get_workload_level(score):
	if score is None:
		return _("Insufficient Data")
	if score > 100:
		return _("Overcommitted")
	if score > 85:
		return _("Critical")
	if score > 75:
		return _("High")
	if score > 60:
		return _("Moderate")
	return _("Healthy")


def get_message():
	return _(
		"Estimated load uses Press inventory and the latest Site Usage only; it does not represent real-time traffic. Application load weighs CPU 40%, RAM 30%, storage 20%, and site density 10%. Database load weighs storage 75% and database density 25%; the higher score is shown. Density references are 20 sites and 50 databases per vCPU."
	)


def get_summary(data):
	scores = [row.workload_score for row in data if row.workload_score is not None]
	return [
		{"label": _("Servers"), "value": len(data), "datatype": "Int"},
		{"label": _("Sites"), "value": sum(row.total_sites for row in data), "datatype": "Int"},
		{
			"label": _("Average Estimated Load"),
			"value": round(sum(scores) / len(scores), 1) if scores else 0,
			"datatype": "Percent",
		},
		{
			"label": _("High Load Servers"),
			"value": sum((row.workload_score or 0) > 75 for row in data),
			"datatype": "Int",
			"indicator": "Red",
		},
	]
