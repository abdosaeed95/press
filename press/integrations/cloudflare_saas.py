# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now

from press.press.doctype.cloudflare_settings.cloudflare_settings import (
	get_cloudflare_settings,
	log_cloudflare_error,
)


def provision_custom_hostname(site_domain):
	settings, root_domain = get_saas_settings()
	try:
		custom_hostname = settings.client().ensure_custom_hostname(
			root_domain.cloudflare_zone_id,
			site_domain.domain,
		)
		update_custom_hostname(site_domain, custom_hostname)
		return custom_hostname
	except Exception as exception:
		set_state(
			site_domain,
			cloudflare_hostname_status="Error",
			cloudflare_error=str(exception),
			cloudflare_last_synced=now(),
		)
		log_cloudflare_error(
			"Cloudflare Custom Hostname Provisioning Error",
			exception,
			site_domain=site_domain.name,
		)
		raise


def reconcile_custom_hostname(site_domain):
	if not site_domain.cloudflare_custom_hostname_id:
		return
	settings, root_domain = get_saas_settings()
	try:
		custom_hostname = settings.client().get_custom_hostname(
			root_domain.cloudflare_zone_id,
			site_domain.cloudflare_custom_hostname_id,
		)
		update_custom_hostname(site_domain, custom_hostname)
	except Exception as exception:
		set_state(
			site_domain,
			cloudflare_hostname_status="Error",
			cloudflare_error=str(exception),
			cloudflare_last_synced=now(),
		)
		log_cloudflare_error(
			"Cloudflare Custom Hostname Reconciliation Error",
			exception,
			site_domain=site_domain.name,
		)
		raise


def delete_custom_hostname(site_domain):
	if not site_domain.cloudflare_custom_hostname_id:
		return
	settings, root_domain = get_saas_settings()
	settings.client().delete_custom_hostname(
		root_domain.cloudflare_zone_id,
		site_domain.cloudflare_custom_hostname_id,
	)


def get_saas_settings():
	settings = get_cloudflare_settings(required=True)
	if not settings.manage_saas or not settings.default_zone:
		frappe.throw(_("Cloudflare for SaaS is not configured."))
	root_domain = frappe.get_doc("Root Domain", settings.default_zone)
	if not root_domain.cloudflare_saas_enabled:
		frappe.throw(_("Cloudflare for SaaS is not enabled for Root Domain {0}.").format(root_domain.name))
	return settings, root_domain


def update_custom_hostname(site_domain, custom_hostname):
	ssl = custom_hostname["ssl"]
	try:
		ownership_verification = custom_hostname["ownership_verification"]
	except KeyError:
		ownership_verification = None
	try:
		ownership_verification_http = custom_hostname["ownership_verification_http"]
	except KeyError:
		ownership_verification_http = None
	try:
		ssl_validation_records = ssl["validation_records"]
	except KeyError:
		ssl_validation_records = []
	verification = {
		"ownership_verification": ownership_verification,
		"ownership_verification_http": ownership_verification_http,
		"ssl_validation_records": ssl_validation_records,
	}
	set_state(
		site_domain,
		cloudflare_custom_hostname_id=custom_hostname["id"],
		cloudflare_hostname_status=custom_hostname["status"],
		cloudflare_ssl_status=ssl["status"],
		cloudflare_verification=frappe.as_json(verification, indent=2),
		cloudflare_error=None,
		cloudflare_last_synced=now(),
	)


def set_state(site_domain, **values):
	frappe.db.set_value(
		"Site Domain",
		site_domain.name,
		values,
		update_modified=False,
	)
	for field, value in values.items():
		site_domain[field] = value
