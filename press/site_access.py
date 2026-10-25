import frappe


def require_site_administrator(doc=None, method=None):
	if frappe.session.user != "Administrator":
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
