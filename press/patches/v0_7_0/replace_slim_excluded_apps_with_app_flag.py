# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

import frappe


def execute():
	if frappe.db.exists("DocType", "Slim Excluded App"):
		excluded_apps = frappe.get_all("Slim Excluded App", pluck="app")
		if excluded_apps:
			frappe.db.set_value(
				"App",
				{"name": ("in", excluded_apps)},
				"exclude_from_slim_images",
				1,
				update_modified=False,
			)

	frappe.delete_doc_if_exists("DocType", "Slim Excluded Apps", force=True)
	frappe.delete_doc_if_exists("DocType", "Slim Excluded App", force=True)
