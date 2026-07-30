# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.password import delete_all_passwords_for


class UpdateSchedulePublicLink(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		enabled: DF.Check
		password_version: DF.Int
		team: DF.Link
		title: DF.Data
		token: DF.Data
	# end: auto-generated types

	def before_insert(self):
		self.token = frappe.generate_hash(length=32)
		self.password_version = 1

	def on_trash(self):
		delete_all_passwords_for(self.doctype, self.name)
