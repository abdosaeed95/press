# Copyright (c) 2021, Frappe and contributors
# For license information, please see license.txt
from __future__ import annotations

import json
from datetime import datetime, timedelta

import boto3
import frappe
from frappe import _
from frappe.core.utils import find
from frappe.model.document import Document

from press.utils import log_error


class RootDomain(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		aws_access_key_id: DF.Data | None
		aws_secret_access_key: DF.Password | None
		cloudflare_cname_target: DF.Data | None
		cloudflare_fallback_origin: DF.Data | None
		cloudflare_saas_enabled: DF.Check
		cloudflare_zone_id: DF.Data | None
		default_cluster: DF.Link
		default_proxy_server: DF.Link | None
		dns_provider: DF.Literal["AWS Route 53", "Cloudflare", "Generic"]
		team: DF.Link | None
	# end: auto-generated types

	def validate(self):
		if self.cloudflare_dns_provider and not self.cloudflare_zone_id:
			frappe.throw(_("Cloudflare Zone ID is required."))
		if self.cloudflare_saas_enabled and not self.cloudflare_dns_provider:
			frappe.throw(_("Cloudflare for SaaS requires the Cloudflare DNS provider."))
		if self.cloudflare_saas_enabled and (
			not self.cloudflare_fallback_origin or not self.cloudflare_cname_target
		):
			frappe.throw(_("SaaS Fallback Origin and SaaS CNAME Target are required."))

	def after_insert(self):
		if self.dns_provider != "Generic" and not frappe.db.exists(
			"TLS Certificate", {"wildcard": True, "domain": self.name}
		):
			frappe.enqueue_doc(
				self.doctype,
				self.name,
				"obtain_root_domain_tls_certificate",
				enqueue_after_commit=True,
			)

	def obtain_root_domain_tls_certificate(self):
		try:
			rsa_key_size = frappe.db.get_value("Press Settings", "Press Settings", "rsa_key_size")
			frappe.get_doc(
				{
					"doctype": "TLS Certificate",
					"wildcard": True,
					"domain": self.name,
					"rsa_key_size": rsa_key_size,
					"provider": "Let's Encrypt",
				}
			).insert()
		except Exception:
			log_error("Root Domain TLS Certificate Exception")

	@property
	def generic_dns_provider(self):
		if not hasattr(self, "_generic_dns_provider"):
			self._generic_dns_provider = self.dns_provider == "Generic"

		return self._generic_dns_provider

	@property
	def cloudflare_dns_provider(self):
		return self.dns_provider == "Cloudflare"

	@property
	def route53_dns_provider(self):
		return self.dns_provider == "AWS Route 53"

	@property
	def cloudflare_client(self):
		from press.press.doctype.cloudflare_settings.cloudflare_settings import (
			get_cloudflare_client,
		)

		return get_cloudflare_client(required=True)

	@frappe.whitelist()
	def setup_cloudflare_saas(self):
		frappe.only_for("System Manager")
		if not self.cloudflare_dns_provider or not self.cloudflare_saas_enabled:
			frappe.throw(_("Enable Cloudflare for SaaS on a Cloudflare Root Domain first."))

		self.cloudflare_client.upsert_dns_record(
			self.cloudflare_zone_id,
			self.cloudflare_cname_target,
			"CNAME",
			self.cloudflare_fallback_origin,
		)
		return self.cloudflare_client.update_fallback_origin(
			self.cloudflare_zone_id,
			self.cloudflare_fallback_origin,
		)

	@property
	def boto3_client(self):
		if not hasattr(self, "_boto3_client"):
			self._boto3_client = boto3.client(
				"route53",
				aws_access_key_id=self.aws_access_key_id,
				aws_secret_access_key=self.get_password("aws_secret_access_key"),
			)
		return self._boto3_client

	@property
	def hosted_zone(self):
		zones = self.boto3_client.list_hosted_zones_by_name()["HostedZones"]
		return find(reversed(zones), lambda x: self.name.endswith(x["Name"][:-1]))["Id"]

	def get_dns_record_pages(self):
		if self.cloudflare_dns_provider:
			records = self.cloudflare_client.list_dns_records(self.cloudflare_zone_id)
			return [
				{
					"ResourceRecordSets": [
						{
							"Id": record["id"],
							"Name": record["name"],
							"Type": record["type"],
							"ResourceRecords": [{"Value": record["content"]}],
						}
						for record in records
					]
				}
			]
		try:
			paginator = self.boto3_client.get_paginator("list_resource_record_sets")
			return paginator.paginate(
				PaginationConfig={"MaxItems": 10000, "PageSize": 300, "StartingToken": "0"},
				HostedZoneId=self.hosted_zone.split("/")[-1],
			)
		except Exception:
			log_error("Route 53 Pagination Error", domain=self.name)

	def delete_dns_records(self, records: list[dict]):
		if self.cloudflare_dns_provider:
			for record in records:
				self.cloudflare_client.delete_dns_record(self.cloudflare_zone_id, record["Id"])
			return
		try:
			changes = []
			for record in records:
				changes.append({"Action": "DELETE", "ResourceRecordSet": record})

			self.boto3_client.change_resource_record_sets(
				ChangeBatch={"Changes": changes}, HostedZoneId=self.hosted_zone
			)

		except Exception:
			log_error("Route 53 Record Deletion Error", domain=self.name)

	def get_sites_being_renamed(self):
		# get sites renamed in Server but doc not renamed in press
		last_hour = datetime.now() - timedelta(hours=1)  # very large bound just to be safe
		renaming_sites = frappe.get_all(
			"Agent Job",
			{"job_type": "Rename Site", "creation": (">=", last_hour)},
			pluck="request_data",
		)
		return [json.loads(d_str)["new_name"] for d_str in renaming_sites]

	def get_active_site_domains(self):
		return frappe.get_all(
			"Site Domain", {"domain": ("like", f"%{self.name}"), "status": "Active"}, pluck="name"
		)

	def get_active_sites(self):
		return frappe.get_all("Site", {"status": ("!=", "Archived"), "domain": self.name}, pluck="name")

	def get_active_domains(self):
		active_domains = self.get_active_sites()
		active_domains.extend(self.get_sites_being_renamed())
		active_domains.extend(self.get_active_site_domains())
		return set(active_domains)

	def get_default_cluster_proxies(self):
		return frappe.get_all(
			"Proxy Server", {"status": "Active", "cluster": self.default_cluster}, pluck="name"
		)

	def remove_unused_cname_records(self):
		proxies, proxy_targets, protected_records = get_proxy_dns_state()

		default_proxies = self.get_default_cluster_proxies()
		if self.cloudflare_dns_provider:
			default_proxies = {
				f"{proxy.cloudflare_tunnel_id}.cfargotunnel.com"
				for proxy in proxies
				if proxy.name in default_proxies and proxy.cloudflare_tunnel_id
			}

		for page in self.get_dns_record_pages():
			to_delete = []

			frappe.db.commit()
			active_domains = self.get_active_domains()

			for record in page["ResourceRecordSets"]:
				if should_delete_cname(
					record,
					proxy_targets,
					protected_records,
					active_domains,
					default_proxies,
				):
					record["Name"] = record["Name"].strip(".")
					to_delete.append(record)
			if to_delete:
				self.delete_dns_records(to_delete)

	def update_dns_records_for_sites(self, sites: list[str], proxy_server: str):
		if self.generic_dns_provider:
			return

		if self.cloudflare_dns_provider:
			tunnel_id = frappe.db.get_value("Proxy Server", proxy_server, "cloudflare_tunnel_id")
			if not tunnel_id:
				frappe.throw(
					_("Cloudflare tunnel is not configured for proxy server {0}.").format(proxy_server)
				)
			for site in sites:
				self.cloudflare_client.upsert_dns_record(
					self.cloudflare_zone_id,
					site,
					"CNAME",
					f"{tunnel_id}.cfargotunnel.com",
				)
			return

		# update records in batches of 500
		batch_size = 500
		for i in range(0, len(sites), batch_size):
			changes = []
			for site in sites[i : i + batch_size]:
				changes.append(
					{
						"Action": "UPSERT",
						"ResourceRecordSet": {
							"Name": site,
							"Type": "CNAME",
							"TTL": 600,
							"ResourceRecords": [{"Value": proxy_server}],
						},
					}
				)

			self.boto3_client.change_resource_record_sets(
				ChangeBatch={"Changes": changes}, HostedZoneId=self.hosted_zone
			)


def cleanup_cname_records():
	domains = frappe.get_all("Root Domain", pluck="name")
	for domain_name in domains:
		domain = RootDomain("Root Domain", domain_name)
		if domain.generic_dns_provider:
			continue

		domain.remove_unused_cname_records()


def get_proxy_dns_state():
	proxies = frappe.get_all(
		"Proxy Server",
		{"status": "Active"},
		["name", "cloudflare_tunnel_id", "cloudflare_ssh_hostname"],
	)
	proxy_targets = {proxy.name for proxy in proxies}
	proxy_targets.update(
		f"{proxy.cloudflare_tunnel_id}.cfargotunnel.com" for proxy in proxies if proxy.cloudflare_tunnel_id
	)
	protected_records = {proxy.name for proxy in proxies}
	protected_records.update(
		proxy.cloudflare_ssh_hostname for proxy in proxies if proxy.cloudflare_ssh_hostname
	)
	return proxies, proxy_targets, protected_records


def should_delete_cname(
	record,
	proxy_targets,
	protected_records,
	active_domains,
	default_proxies,
):
	if record["Type"] != "CNAME":
		return False
	value = record["ResourceRecords"][0]["Value"].rstrip(".")
	domain = record["Name"].strip(".")
	if value not in proxy_targets:
		return False
	if domain.startswith("*.") or domain in protected_records:
		return False
	return domain not in active_domains or value in default_proxies
