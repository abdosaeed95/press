# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

import frappe

from press.utils import CAIRO_TIMEZONE


def execute():
	frappe.db.set_single_value("System Settings", "time_zone", CAIRO_TIMEZONE)
