# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

from __future__ import annotations

from typing import Any

import frappe
import requests
from frappe import _
from frappe.exceptions import ValidationError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class CloudflareError(ValidationError):
	pass


class Cloudflare:
	def __init__(self, api_token: str, account_id: str | None = None):
		self.account_id = account_id
		self.session = requests.Session()
		self.session.headers.update(
			{
				"Authorization": f"Bearer {api_token}",
				"Content-Type": "application/json",
			}
		)
		self.session.mount(
			"https://",
			HTTPAdapter(
				max_retries=Retry(
					total=3,
					backoff_factor=1,
					status_forcelist=(429, 500, 502, 503, 504),
					allowed_methods=("DELETE", "GET", "PATCH", "PUT"),
					respect_retry_after_header=True,
				)
			),
		)

	def request(
		self,
		method: str,
		path: str,
		params: dict[str, Any] | None = None,
		data: dict[str, Any] | None = None,
	) -> Any:
		payload = self._request(method, path, params=params, data=data)
		return payload["result"] if "result" in payload else None

	def paginated(self, path: str, params: dict[str, Any] | None = None) -> list[dict]:
		page = 1
		result = []
		params = {**(params or {}), "per_page": 100}
		while True:
			payload = self._request("GET", path, params={**params, "page": page})
			rows = payload["result"] if "result" in payload else []
			result.extend(rows)
			result_info = payload["result_info"] if "result_info" in payload else {}
			total_pages = result_info["total_pages"] if "total_pages" in result_info else None
			if not rows or (total_pages and page >= total_pages) or len(rows) < params["per_page"]:
				return result
			page += 1

	def _request(
		self,
		method: str,
		path: str,
		params: dict[str, Any] | None = None,
		data: dict[str, Any] | None = None,
	) -> dict:
		try:
			response = self.session.request(
				method,
				f"https://api.cloudflare.com/client/v4/{path.lstrip('/')}",
				params=params,
				json=data,
				timeout=30,
			)
			payload = response.json()
		except (requests.RequestException, ValueError) as exception:
			frappe.throw(
				_("Unable to reach Cloudflare: {0}").format(exception),
				exc=CloudflareError,
			)

		if response.ok and ("success" not in payload or payload["success"]):
			return payload

		errors = payload["errors"] if "errors" in payload else []
		message = "; ".join(error["message"] if "message" in error else str(error) for error in errors)
		frappe.throw(
			_("Cloudflare request failed with status {0}: {1}").format(
				response.status_code, message or response.text
			),
			exc=CloudflareError,
		)
		return {}

	def verify_token(self) -> dict:
		return self.request("GET", "user/tokens/verify")

	def list_accounts(self) -> list[dict]:
		return self.paginated("accounts")

	def list_zones(self, name: str | None = None) -> list[dict]:
		params = {"account.id": self.account_id}
		if name:
			params["name"] = name
		return self.paginated("zones", params)

	def get_zone(self, name: str) -> dict | None:
		return next((zone for zone in self.list_zones(name) if zone["name"] == name), None)

	def create_zone(self, name: str) -> dict:
		return self.request(
			"POST",
			"zones",
			data={"name": name, "account": {"id": self._account_id()}},
		)

	def search_domains(self, query: str, extensions: list[str] | None = None, limit: int = 20) -> list[dict]:
		params: dict[str, Any] = {"q": query, "limit": min(limit, 50)}
		if extensions:
			params["extensions"] = extensions
		result = self.request("GET", f"accounts/{self._account_id()}/registrar/domain-search", params=params)
		return result["domains"] if "domains" in result else []

	def check_domains(self, domains: list[str]) -> list[dict]:
		result = self.request(
			"POST",
			f"accounts/{self._account_id()}/registrar/domain-check",
			data={"domains": domains[:20]},
		)
		return result["domains"] if "domains" in result else []

	def register_domain(self, domain: str) -> dict:
		return self.request(
			"POST",
			f"accounts/{self._account_id()}/registrar/registrations",
			data={"domain_name": domain},
		)

	def list_dns_records(
		self,
		zone_id: str,
		name: str | None = None,
		record_type: str | None = None,
		content: str | None = None,
	) -> list[dict]:
		params = {}
		if name:
			params["name.exact"] = name
		if record_type:
			params["type"] = record_type
		if content:
			params["content"] = content
		return self.paginated(f"zones/{zone_id}/dns_records", params)

	def upsert_dns_record(
		self,
		zone_id: str,
		name: str,
		record_type: str,
		content: str,
		proxied: bool = True,
		ttl: int = 1,
	) -> dict:
		records = self.list_dns_records(zone_id, name, record_type)
		data = {
			"name": name,
			"type": record_type,
			"content": content,
			"proxied": proxied,
			"ttl": ttl,
			"comment": "Managed by Press",
		}
		if len(records) > 1:
			frappe.throw(
				_("Multiple {0} records exist for {1}.").format(record_type, name),
				exc=CloudflareError,
			)
		if records:
			return self.request("PUT", f"zones/{zone_id}/dns_records/{records[0]['id']}", data=data)
		return self.request("POST", f"zones/{zone_id}/dns_records", data=data)

	def delete_dns_record(self, zone_id: str, record_id: str) -> dict:
		return self.request("DELETE", f"zones/{zone_id}/dns_records/{record_id}")

	def delete_dns_records(self, zone_id: str, name: str, record_type: str | None = None):
		for record in self.list_dns_records(zone_id, name, record_type):
			self.delete_dns_record(zone_id, record["id"])

	def list_tunnels(self, name: str | None = None) -> list[dict]:
		params = {"is_deleted": "false"}
		if name:
			params["name"] = name
		return self.paginated(f"accounts/{self._account_id()}/cfd_tunnel", params)

	def ensure_tunnel(self, name: str) -> dict:
		tunnels = [tunnel for tunnel in self.list_tunnels(name) if tunnel["name"] == name]
		if len(tunnels) > 1:
			frappe.throw(
				_("Multiple Cloudflare tunnels are named {0}.").format(name),
				exc=CloudflareError,
			)
		if tunnels:
			return tunnels[0]
		return self.request(
			"POST",
			f"accounts/{self._account_id()}/cfd_tunnel",
			data={"name": name, "config_src": "cloudflare"},
		)

	def get_tunnel(self, tunnel_id: str) -> dict:
		return self.request("GET", f"accounts/{self._account_id()}/cfd_tunnel/{tunnel_id}")

	def get_tunnel_token(self, tunnel_id: str) -> str:
		return self.request("GET", f"accounts/{self._account_id()}/cfd_tunnel/{tunnel_id}/token")

	def set_tunnel_configuration(self, tunnel_id: str, ingress: list[dict]) -> dict:
		return self.request(
			"PUT",
			f"accounts/{self._account_id()}/cfd_tunnel/{tunnel_id}/configurations",
			data={"config": {"ingress": ingress}},
		)

	def disconnect_tunnel(self, tunnel_id: str):
		return self.request("DELETE", f"accounts/{self._account_id()}/cfd_tunnel/{tunnel_id}/connections")

	def delete_tunnel(self, tunnel_id: str):
		return self.request(
			"DELETE",
			f"accounts/{self._account_id()}/cfd_tunnel/{tunnel_id}",
			params={"cascade": "true"},
		)

	def list_access_service_tokens(self) -> list[dict]:
		return self.paginated(f"accounts/{self._account_id()}/access/service_tokens")

	def create_access_service_token(self, name: str) -> dict:
		return self.request(
			"POST",
			f"accounts/{self._account_id()}/access/service_tokens",
			data={"name": name, "duration": "8760h"},
		)

	def rotate_access_service_token(self, token_id: str) -> dict:
		return self.request(
			"POST",
			f"accounts/{self._account_id()}/access/service_tokens/{token_id}/rotate",
		)

	def list_access_applications(self) -> list[dict]:
		return self.paginated(f"accounts/{self._account_id()}/access/apps")

	def ensure_access_application(self, name: str, domain: str, service_token_id: str) -> dict:
		applications = [
			application
			for application in self.list_access_applications()
			if "domain" in application and application["domain"] == domain
		]
		if applications:
			application = applications[0]
		else:
			application = self.request(
				"POST",
				f"accounts/{self._account_id()}/access/apps",
				data={
					"name": name,
					"domain": domain,
					"type": "self_hosted",
					"session_duration": "24h",
				},
			)

		policies = self.paginated(f"accounts/{self._account_id()}/access/apps/{application['id']}/policies")
		if not any("name" in policy and policy["name"] == "Press automation" for policy in policies):
			self.request(
				"POST",
				f"accounts/{self._account_id()}/access/apps/{application['id']}/policies",
				data={
					"name": "Press automation",
					"decision": "non_identity",
					"precedence": 1,
					"include": [{"service_token": {"token_id": service_token_id}}],
				},
			)
		return application

	def delete_access_application(self, application_id: str):
		return self.request(
			"DELETE",
			f"accounts/{self._account_id()}/access/apps/{application_id}",
		)

	def list_custom_hostnames(self, zone_id: str, hostname: str | None = None) -> list[dict]:
		params = {"hostname": hostname} if hostname else None
		return self.paginated(f"zones/{zone_id}/custom_hostnames", params)

	def update_fallback_origin(self, zone_id: str, origin: str) -> dict:
		return self.request(
			"PUT",
			f"zones/{zone_id}/custom_hostnames/fallback_origin",
			data={"origin": origin},
		)

	def ensure_custom_hostname(
		self, zone_id: str, hostname: str, custom_origin_server: str | None = None
	) -> dict:
		hostnames = [
			custom_hostname
			for custom_hostname in self.list_custom_hostnames(zone_id, hostname)
			if custom_hostname["hostname"] == hostname
		]
		if hostnames:
			return hostnames[0]
		data: dict[str, Any] = {
			"hostname": hostname,
			"ssl": {"method": "txt", "type": "dv"},
			"custom_metadata": {"managed_by": "press"},
		}
		if custom_origin_server:
			data["custom_origin_server"] = custom_origin_server
		return self.request("POST", f"zones/{zone_id}/custom_hostnames", data=data)

	def get_custom_hostname(self, zone_id: str, custom_hostname_id: str) -> dict:
		return self.request("GET", f"zones/{zone_id}/custom_hostnames/{custom_hostname_id}")

	def delete_custom_hostname(self, zone_id: str, custom_hostname_id: str):
		return self.request("DELETE", f"zones/{zone_id}/custom_hostnames/{custom_hostname_id}")

	def _account_id(self) -> str:
		if not self.account_id:
			frappe.throw(_("Cloudflare account ID is required."), exc=CloudflareError)
		return self.account_id
