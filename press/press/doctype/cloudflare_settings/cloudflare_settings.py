# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

from __future__ import annotations

from typing import TYPE_CHECKING

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, now
from frappe.utils.synchronization import filelock

from press.integrations.cloudflare import Cloudflare, CloudflareError

if TYPE_CHECKING:
	from frappe.types import DF


class CloudflareSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	if TYPE_CHECKING:
		access_service_token_client_id: DF.Data | None
		access_service_token_id: DF.Data | None
		access_service_token_secret: DF.Password | None
		account_id: DF.Data
		account_name: DF.Data | None
		api_token: DF.Password
		default_zone: DF.Link | None
		enabled: DF.Check
		last_verified: DF.Datetime | None
		manage_access: DF.Check
		manage_dns: DF.Check
		manage_saas: DF.Check
		manage_tunnels: DF.Check
		registrar_enabled: DF.Check
		tunnel_name_prefix: DF.Data
	# end: auto-generated types

	def validate(self):
		if self.enabled and not self.get_password("api_token", raise_exception=False):
			frappe.throw(_("Cloudflare API token is required when the integration is enabled."))
		if self.enabled and not self.account_id:
			frappe.throw(_("Cloudflare account ID is required when the integration is enabled."))
		if (
			self.default_zone
			and frappe.db.get_value("Root Domain", self.default_zone, "dns_provider") != "Cloudflare"
		):
			frappe.throw(_("Default Zone must use the Cloudflare DNS provider."))

	def client(self) -> Cloudflare:
		if not self.enabled:
			frappe.throw(_("Cloudflare integration is disabled."))
		return Cloudflare(self.get_password("api_token"), self.account_id)

	@frappe.whitelist()
	def test_connection(self):
		frappe.only_for("System Manager")
		client = self.client()
		token = client.verify_token()
		account = next(
			(account for account in client.list_accounts() if account["id"] == self.account_id),
			None,
		)
		if not account:
			frappe.throw(_("The configured API token cannot access account {0}.").format(self.account_id))
		self.db_set("account_name", account["name"])
		self.db_set("last_verified", now())
		return {
			"account": account,
			"token_status": token["status"] if "status" in token else None,
			"zones": len(client.list_zones()),
		}

	@frappe.whitelist()
	def get_accounts(self):
		frappe.only_for("System Manager")
		return self.client().list_accounts()

	@frappe.whitelist()
	def get_zones(self):
		frappe.only_for("System Manager")
		return self.client().list_zones()

	@frappe.whitelist()
	def import_zone(self, domain: str, default_cluster: str):
		frappe.only_for("System Manager")
		zone = self.client().get_zone(domain)
		if not zone:
			frappe.throw(_("Cloudflare zone {0} was not found.").format(domain))
		if frappe.db.exists("Root Domain", domain):
			root_domain = frappe.get_doc("Root Domain", domain)
		else:
			root_domain = frappe.new_doc("Root Domain")
			root_domain.update(
				{
					"name": domain,
					"default_cluster": default_cluster,
				}
			)
		root_domain.dns_provider = "Cloudflare"
		root_domain.cloudflare_zone_id = zone["id"]
		root_domain.save()
		if not self.default_zone:
			self.db_set("default_zone", root_domain.name)
		return root_domain.name

	@frappe.whitelist()
	def search_domains(self, query: str, extensions: str | list[str] | None = None):
		frappe.only_for("System Manager")
		self.validate_registrar()
		if isinstance(extensions, str):
			extensions = frappe.parse_json(extensions)
		return self.client().search_domains(query, extensions)

	@frappe.whitelist()
	def check_domains(self, domains: str | list[str]):
		frappe.only_for("System Manager")
		self.validate_registrar()
		if isinstance(domains, str):
			domains = frappe.parse_json(domains)
		return self.client().check_domains(domains)

	@frappe.whitelist()
	def register_domain(
		self,
		domain: str,
		expected_price: str,
		expected_currency: str,
		confirm_registration: int = 0,
	):
		frappe.only_for("System Manager")
		self.validate_registrar()
		if not cint(confirm_registration):
			frappe.throw(_("Confirm the domain registration before continuing."))
		result = self.client().check_domains([domain])
		if not result or "registrable" not in result[0] or not result[0]["registrable"]:
			frappe.throw(_("Domain {0} is not available for registration.").format(domain))
		pricing = result[0]["pricing"]
		if (
			str(pricing["registration_cost"]) != str(expected_price)
			or pricing["currency"] != expected_currency
		):
			frappe.throw(
				_("The registration price changed to {0} {1}. Confirm the new price.").format(
					pricing["registration_cost"], pricing["currency"]
				)
			)
		return self.client().register_domain(domain)

	def validate_registrar(self):
		if not self.registrar_enabled:
			frappe.throw(_("Cloudflare Registrar is not enabled."))

	def ensure_access_service_token(self) -> tuple[str, str, str]:
		with filelock("cloudflare-access-service-token"):
			self.reload()
			return self._ensure_access_service_token()

	def _ensure_access_service_token(self) -> tuple[str, str, str]:
		client_id = self.access_service_token_client_id
		client_secret = self.get_password("access_service_token_secret", raise_exception=False)
		if self.access_service_token_id and client_id and client_secret:
			return self.access_service_token_id, client_id, client_secret

		token = self.client().create_access_service_token(f"{self.tunnel_name_prefix}-automation")
		self.db_set("access_service_token_id", token["id"])
		self.db_set("access_service_token_client_id", token["client_id"])
		self.access_service_token_secret = token["client_secret"]
		self.save()
		return token["id"], token["client_id"], token["client_secret"]

	@frappe.whitelist()
	def rotate_access_service_token(self):
		frappe.only_for("System Manager")
		if not self.access_service_token_id:
			self.ensure_access_service_token()
			return
		token = self.client().rotate_access_service_token(self.access_service_token_id)
		self.db_set("access_service_token_client_id", token["client_id"])
		self.access_service_token_secret = token["client_secret"]
		self.save()


def get_cloudflare_settings(required: bool = False) -> CloudflareSettings | None:
	settings = frappe.get_single("Cloudflare Settings")
	if settings.enabled:
		return settings
	if required:
		frappe.throw(_("Cloudflare integration is not configured."))
	return None


@frappe.whitelist()
def discover_accounts(api_token: str):
	frappe.only_for("System Manager")
	return Cloudflare(api_token).list_accounts()


def get_cloudflare_client(required: bool = False) -> Cloudflare | None:
	settings = get_cloudflare_settings(required)
	return settings.client() if settings else None


def log_cloudflare_error(title: str, exception: Exception, **context):
	if isinstance(exception, CloudflareError):
		frappe.log_error(
			title=title,
			message=frappe.as_json({"error": str(exception), **context}, indent=2),
		)
		return
	frappe.log_error(title=title, message=frappe.get_traceback())
