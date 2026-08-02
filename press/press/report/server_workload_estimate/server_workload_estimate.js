// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

frappe.query_reports['Server Workload Estimate'] = {
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname !== 'workload_level') return value;

		let color = 'green';
		if (data.workload_score == null) color = 'gray';
		else if (data.workload_score > 75) color = 'red';
		else if (data.workload_score > 60) color = 'orange';
		return `<span class="indicator-pill ${color}">${value}</span>`;
	},
};
