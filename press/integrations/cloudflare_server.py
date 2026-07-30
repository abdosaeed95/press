# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

from __future__ import annotations

import re
import shlex

import frappe
from frappe import _
from frappe.utils import now
from frappe.utils.synchronization import filelock

from press.press.doctype.cloudflare_settings.cloudflare_settings import (
	get_cloudflare_settings,
	log_cloudflare_error,
)
from press.runner import Ansible

SERVER_DOCTYPES = ("Server", "Database Server", "Proxy Server")


def provision_server(server, install=True):
	with filelock(f"cloudflare-{server.doctype}-{server.name}"):
		return _provision_server(server, install)


def _provision_server(server, install):
	settings = get_cloudflare_settings(required=True)
	if not settings.manage_tunnels or not settings.manage_dns:
		frappe.throw(_("Cloudflare tunnel and DNS management must be enabled."))

	root_domain = get_root_domain(server)
	client = settings.client()
	set_state(server, cloudflare_tunnel_status="Pending", cloudflare_error=None)
	update_self_hosted_status(server, "Pending")

	try:
		tunnel = client.ensure_tunnel(tunnel_name(server, settings.tunnel_name_prefix))
		ssh_hostname = get_ssh_hostname(server, root_domain.name)
		ingress, routes = get_routes(server, root_domain, ssh_hostname)
		client.set_tunnel_configuration(tunnel["id"], ingress)

		for domain, hostname in routes:
			client.upsert_dns_record(
				domain.cloudflare_zone_id,
				hostname,
				"CNAME",
				f"{tunnel['id']}.cfargotunnel.com",
			)

		access_application_id = None
		if settings.manage_access:
			service_token_id, _, _ = settings.ensure_access_service_token()
			application = client.ensure_access_application(
				f"{settings.tunnel_name_prefix}-{server.name}-ssh",
				ssh_hostname,
				service_token_id,
			)
			access_application_id = application["id"]

		set_state(
			server,
			cloudflare_tunnel_id=tunnel["id"],
			cloudflare_ssh_hostname=ssh_hostname,
			cloudflare_access_application_id=access_application_id,
		)

		if install:
			if not server.ip:
				frappe.throw(
					_("The server has no bootstrap IP. Run the Cloudflare bootstrap command on the server.")
				)
			play = Ansible(
				server=server,
				playbook="cloudflare_tunnel.yml",
				user=server._ssh_user(),
				port=server._ssh_port(),
				sensitive_variables={"cloudflare_tunnel_token": client.get_tunnel_token(tunnel["id"])},
				use_cloudflare=False,
			).run()
			if play.status != "Success":
				frappe.throw(_("Cloudflare Tunnel installation failed."))

		return refresh_server(server)
	except Exception as exception:
		set_state(
			server,
			cloudflare_tunnel_status="Error",
			cloudflare_error=str(exception),
		)
		update_self_hosted_status(server, "Error")
		log_cloudflare_error(
			"Cloudflare Server Provisioning Error",
			exception,
			server=server.name,
			server_type=server.doctype,
		)
		raise


def refresh_server(server):
	if not server.cloudflare_tunnel_id:
		set_state(server, cloudflare_tunnel_status="Inactive")
		update_self_hosted_status(server, "Inactive")
		return "Inactive"

	try:
		tunnel = get_cloudflare_settings(required=True).client().get_tunnel(server.cloudflare_tunnel_id)
		statuses = {
			"healthy": "Healthy",
			"degraded": "Degraded",
			"down": "Error",
			"inactive": "Inactive",
		}
		try:
			status = statuses[tunnel["status"]]
		except KeyError:
			status = "Pending"
		set_state(
			server,
			cloudflare_tunnel_status=status,
			cloudflare_error=None,
			cloudflare_last_synced=now(),
		)
		update_self_hosted_status(server, status)
		return status
	except Exception as exception:
		set_state(
			server,
			cloudflare_tunnel_status="Error",
			cloudflare_error=str(exception),
			cloudflare_last_synced=now(),
		)
		update_self_hosted_status(server, "Error")
		log_cloudflare_error(
			"Cloudflare Tunnel Reconciliation Error",
			exception,
			server=server.name,
			server_type=server.doctype,
		)
		raise


def revoke_server(server):
	with filelock(f"cloudflare-{server.doctype}-{server.name}"):
		return _revoke_server(server)


def _revoke_server(server):
	if not server.cloudflare_tunnel_id:
		return

	settings = get_cloudflare_settings(required=True)
	client = settings.client()
	target = f"{server.cloudflare_tunnel_id}.cfargotunnel.com"

	for domain in frappe.get_all(
		"Root Domain",
		{"dns_provider": "Cloudflare", "cloudflare_zone_id": ("is", "set")},
		["cloudflare_zone_id"],
	):
		for record in client.list_dns_records(
			domain.cloudflare_zone_id,
			record_type="CNAME",
			content=target,
		):
			if record["content"].rstrip(".") == target:
				client.delete_dns_record(domain.cloudflare_zone_id, record["id"])

	if server.cloudflare_access_application_id:
		client.delete_access_application(server.cloudflare_access_application_id)

	client.disconnect_tunnel(server.cloudflare_tunnel_id)
	client.delete_tunnel(server.cloudflare_tunnel_id)
	set_state(
		server,
		cloudflare_tunnel_id=None,
		cloudflare_ssh_hostname=None,
		cloudflare_access_application_id=None,
		cloudflare_tunnel_status="Inactive",
		cloudflare_error=None,
		cloudflare_last_synced=now(),
	)
	update_self_hosted_status(server, "Inactive")


def get_bootstrap_command(server):
	frappe.only_for("System Manager")
	provision_server(server, install=False)
	token = get_cloudflare_settings(required=True).client().get_tunnel_token(server.cloudflare_tunnel_id)
	return (
		"arch=$(dpkg --print-architecture) && "
		'curl -fsSL "https://github.com/cloudflare/cloudflared/releases/latest/download/'
		'cloudflared-linux-${arch}.deb" -o /tmp/cloudflared.deb && '
		"sudo apt-get install -y /tmp/cloudflared.deb && "
		"(sudo cloudflared service uninstall >/dev/null 2>&1 || true) && "
		f"sudo cloudflared service install {shlex.quote(token)}"
	)


def get_root_domain(server):
	if not server.cloudflare_zone:
		frappe.throw(_("Select a Cloudflare Zone before provisioning the tunnel."))
	root_domain = frappe.get_doc("Root Domain", server.cloudflare_zone)
	if not root_domain.cloudflare_dns_provider:
		frappe.throw(_("Root Domain {0} is not managed by Cloudflare.").format(root_domain.name))
	return root_domain


def get_routes(server, root_domain, ssh_hostname):
	routes = [(root_domain, ssh_hostname)]
	ingress = [{"hostname": ssh_hostname, "service": f"ssh://localhost:{server._ssh_port()}"}]

	if server.doctype != "Database Server":
		add_https_route(ingress, routes, root_domain, server.name)

	if server.doctype == "Proxy Server":
		for row in server.domains:
			domain = frappe.get_doc("Root Domain", row.domain)
			if domain.cloudflare_dns_provider:
				add_https_route(ingress, routes, domain, f"*.{domain.name}")

	ingress.append({"service": "http_status:404"})
	return ingress, routes


def add_https_route(ingress, routes, domain, hostname):
	ingress.append(
		{
			"hostname": hostname,
			"service": "https://localhost:443",
			"originRequest": {"noTLSVerify": True},
		}
	)
	routes.append((domain, hostname))


def get_ssh_hostname(server, zone):
	role = {
		"Server": "app",
		"Database Server": "db",
		"Proxy Server": "proxy",
	}[server.doctype]
	suffix = f"-{role}-ssh"
	label = re.sub(r"[^a-z0-9-]", "-", server.name.lower()).strip("-")[: 63 - len(suffix)]
	return f"{label}{suffix}.{zone}"


def tunnel_name(server, prefix):
	name = re.sub(r"[^a-zA-Z0-9_-]", "-", f"{prefix}-{server.doctype}-{server.name}")
	return name[:100]


def set_state(server, **values):
	frappe.db.set_value(server.doctype, server.name, values, update_modified=False)
	for field, value in values.items():
		server[field] = value


def update_self_hosted_status(server, status):
	if not server.is_self_hosted:
		return
	filters = {
		{
			"Server": "server",
			"Database Server": "database_server",
			"Proxy Server": "proxy_server",
		}[server.doctype]: server.name
	}
	self_hosted = frappe.db.get_value(
		"Self Hosted Server",
		filters,
		["name", "server", "database_server", "proxy_server"],
		as_dict=True,
	)
	if self_hosted:
		statuses = [status]
		if self_hosted.server and self_hosted.server != server.name:
			statuses.append(
				frappe.db.get_value(
					"Server",
					self_hosted.server,
					"cloudflare_tunnel_status",
				)
			)
		if self_hosted.database_server and self_hosted.database_server != server.name:
			statuses.append(
				frappe.db.get_value(
					"Database Server",
					self_hosted.database_server,
					"cloudflare_tunnel_status",
				)
			)
		if self_hosted.proxy_server and self_hosted.proxy_server != server.name:
			statuses.append(
				frappe.db.get_value(
					"Proxy Server",
					self_hosted.proxy_server,
					"cloudflare_tunnel_status",
				)
			)
		statuses = [value for value in statuses if value]
		aggregate_status = next(
			(value for value in ("Error", "Degraded", "Pending", "Inactive", "Healthy") if value in statuses),
			status,
		)
		frappe.db.set_value(
			"Self Hosted Server",
			self_hosted.name,
			{
				"cloudflare_tunnel_status": aggregate_status,
				"cloudflare_last_synced": now(),
			},
			update_modified=False,
		)


def reconcile_cloudflare():
	settings = get_cloudflare_settings()
	if not settings:
		return

	for doctype in SERVER_DOCTYPES:
		for name in frappe.get_all(
			doctype,
			{"behind_cloudflare": 1, "status": ("!=", "Archived")},
			pluck="name",
		):
			frappe.enqueue(
				"press.integrations.cloudflare_server.reconcile_server",
				doctype=doctype,
				name=name,
				enqueue_after_commit=True,
			)

	for name in frappe.get_all(
		"Site Domain",
		{"cloudflare_custom_hostname_id": ("is", "set")},
		pluck="name",
	):
		frappe.enqueue_doc(
			"Site Domain",
			name,
			"reconcile_cloudflare",
			enqueue_after_commit=True,
		)

	for name in frappe.get_all(
		"Root Domain",
		{"dns_provider": "Cloudflare", "cloudflare_saas_enabled": 1},
		pluck="name",
	):
		frappe.enqueue_doc(
			"Root Domain",
			name,
			"setup_cloudflare_saas",
			enqueue_after_commit=True,
		)


def reconcile_server(doctype, name):
	provision_server(frappe.get_doc(doctype, name), install=False)
