# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

from __future__ import annotations

from typing import TYPE_CHECKING

import frappe
from frappe import _
from frappe.frappeclient import FrappeClient
from frappe.model.document import Document

if TYPE_CHECKING:
	from frappe.types import DF


class ConsoleIntegrationSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	if TYPE_CHECKING:
		console_url: DF.Data
		password: DF.Password
		username: DF.Data
	# end: auto-generated types

	def get_sites_without_slaves(self, sites: list[str]) -> list[str]:
		password = self.get_password("password", raise_exception=False)
		if not (self.console_url and self.username and password):
			frappe.throw(_("Configure Console Integration Settings before selecting sites for update."))

		with FrappeClient(self.console_url.rstrip("/"), self.username, password) as client:
			masters = client.get_list(
				"Instance",
				fields=["name", "subscription"],
				filters={
					"name": ["in", sites],
					"instance_type": "Master",
					"status": ["!=", "Archived"],
				},
				limit_page_length=len(sites),
			)
			subscriptions = [master["subscription"] for master in masters if master.get("subscription")]
			slaves = (
				client.get_list(
					"Instance",
					fields=["subscription"],
					filters={
						"subscription": ["in", subscriptions],
						"instance_type": "Slave",
						"setup_complete": 1,
						"status": ["not in", ["Archived", "Archiving"]],
					},
					limit_page_length=10000,
				)
				if subscriptions
				else []
			)

		slave_subscriptions = {slave["subscription"] for slave in slaves}
		master_subscriptions = {master["name"]: master.get("subscription") for master in masters}
		return [site for site in sites if master_subscriptions.get(site) not in slave_subscriptions]
