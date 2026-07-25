# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class SlimExcludedApps(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from press.press.doctype.slim_excluded_app.slim_excluded_app import SlimExcludedApp

		excluded_apps: DF.Table[SlimExcludedApp]
	# end: auto-generated types

	def validate(self):
		if any(row.app == "frappe" for row in self.excluded_apps):
			frappe.throw(_("Frappe cannot be excluded from slim images."))


def get_slim_excluded_apps() -> list[str]:
	if not frappe.db.exists("DocType", "Slim Excluded Apps"):
		return []

	return [row.app for row in frappe.get_cached_doc("Slim Excluded Apps").excluded_apps]
