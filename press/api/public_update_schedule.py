# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import cint, get_datetime, now
from frappe.utils.password import check_password, update_password

from press.api.account import get_permission_roles
from press.api.update_schedule import get_updates
from press.utils import get_current_team

DOCTYPE = "Update Schedule Public Link"
ACCESS_TOKEN_TTL = 6 * 60 * 60
MAX_SCHEDULE_DAYS = 62


@frappe.whitelist()
def get_links():
	team = get_management_team()
	return frappe.get_all(
		DOCTYPE,
		{"team": team},
		["name", "title", "token", "enabled", "creation", "modified"],
		order_by="creation desc",
	)


@frappe.whitelist(methods=["POST"])
def create_link(title: str):
	team = get_management_team()
	title = title.strip()
	if not title:
		frappe.throw(_("Title is required."))

	link = frappe.get_doc(
		{
			"doctype": DOCTYPE,
			"title": title,
			"team": team,
			"enabled": 1,
		}
	).insert(ignore_permissions=True)
	password = generate_password()
	update_password(link.name, password, DOCTYPE)
	return serialize_link(link, password)


@frappe.whitelist(methods=["POST"])
def change_password(name: str, password: str | None = None):
	link = get_managed_link(name)
	password = password.strip() if password else generate_password()
	if len(password) < 8:
		frappe.throw(_("Password must contain at least 8 characters."))

	update_password(link.name, password, DOCTYPE)
	frappe.db.set_value(DOCTYPE, link.name, "password_version", cint(link.password_version) + 1)
	return {"password": password}


@frappe.whitelist(methods=["POST"])
def set_enabled(name: str, enabled: int):
	link = get_managed_link(name)
	frappe.db.set_value(
		DOCTYPE,
		link.name,
		{
			"enabled": cint(enabled),
			"password_version": cint(link.password_version) + 1,
		},
	)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="token", limit=5, seconds=5 * 60)
def unlock(token: str, password: str):
	link = get_public_link(token)
	try:
		check_password(link.name, password, DOCTYPE, delete_tracker_cache=False)
	except frappe.AuthenticationError:
		frappe.throw(_("Invalid link or password."), frappe.AuthenticationError)

	access_token = frappe.generate_hash(length=32)
	frappe.cache.set_value(
		access_key(token, access_token),
		link.password_version,
		expires_in_sec=ACCESS_TOKEN_TTL,
	)
	return {"access_token": access_token, "title": link.title}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="token", limit=120, seconds=60)
def get_public_schedule(token: str, access_token: str, start: str, end: str):
	link = get_public_link(token)
	if cint(frappe.cache.get_value(access_key(token, access_token))) != cint(link.password_version):
		frappe.throw(_("This public schedule session has expired."), frappe.AuthenticationError)

	start = get_datetime(start)
	end = get_datetime(end)
	if end <= start:
		frappe.throw(_("Schedule end must be after schedule start."))
	if (end - start).total_seconds() > MAX_SCHEDULE_DAYS * 24 * 60 * 60:
		frappe.throw(_("Public schedule ranges cannot exceed 62 days."))

	return {
		"title": link.title,
		"last_refreshed": now(),
		"updates": [
			{
				"site": update.site,
				"status": update.status,
				"scheduled_time": update.scheduled_time,
				"update_start": update.update_start,
				"update_end": update.update_end,
				"update_duration": update.update_duration,
				"event_time": update.event_time,
			}
			for update in get_updates(start, end, link.team)
		],
	}


def get_management_team():
	team = get_current_team(get_doc=True)
	if (
		frappe.session.user == "Administrator"
		or frappe.session.user == team.user
		or frappe.db.get_value("User", frappe.session.user, "user_type") == "System User"
		or any(role.admin_access for role in get_permission_roles())
	):
		return team.name
	frappe.throw(
		_("Only the team owner or an administrator can manage public schedule links."), frappe.PermissionError
	)
	return None


def get_managed_link(name: str):
	team = get_management_team()
	link = frappe.db.get_value(
		DOCTYPE,
		{"name": name, "team": team},
		["name", "password_version"],
		as_dict=True,
	)
	if not link:
		frappe.throw(_("Public schedule link not found."), frappe.DoesNotExistError)
	return link


def get_public_link(token: str):
	link = frappe.db.get_value(
		DOCTYPE,
		{"token": token, "enabled": 1},
		["name", "title", "team", "password_version"],
		as_dict=True,
	)
	if not link:
		frappe.throw(_("Invalid link or password."), frappe.AuthenticationError)
	return link


def serialize_link(link, password: str):
	return {
		"name": link.name,
		"title": link.title,
		"token": link.token,
		"enabled": link.enabled,
		"password": password,
	}


def generate_password():
	return frappe.generate_hash(length=32)


def access_key(token: str, access_token: str):
	return f"public-update-schedule:{token}:{access_token}"
