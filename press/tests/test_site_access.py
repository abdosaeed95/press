import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from press import auth, site_access


class TestSiteAccess(unittest.TestCase):
	def setUp(self):
		self.frappe = SimpleNamespace(
			session=SimpleNamespace(user="service@example.com"),
			get_roles=Mock(return_value=["Fodista Cloud MCP"]),
			get_cached_value=Mock(return_value="System User"),
			request=SimpleNamespace(path="/api/method/fodista_cloud_mcp", method="POST"),
			form_dict=SimpleNamespace(cmd=None),
			throw=Mock(side_effect=PermissionError),
			PermissionError=PermissionError,
			_=lambda text: text,
		)
		self.addCleanup(patch.stopall)
		patch.object(auth, "frappe", self.frappe).start()
		patch.object(site_access, "frappe", self.frappe).start()

	def test_only_exact_administrator_identity_can_delete_or_reset(self):
		for user in ("Guest", "manager@example.com", "service@example.com", "administrator"):
			with self.subTest(user=user):
				self.frappe.session.user = user
				self.frappe.get_roles.return_value = ["Administrator", "System Manager"]
				with self.assertRaises(PermissionError):
					site_access.require_site_administrator()
		self.frappe.session.user = "Administrator"
		self.assertIsNone(site_access.require_site_administrator())

	def test_administrator_is_not_restricted_by_implicit_roles(self):
		self.frappe.session.user = "Administrator"
		self.frappe.request.path = "/api/resource/User"
		self.assertIsNone(auth.hook())
		self.frappe.throw.assert_not_called()

	def test_service_account_can_call_mcp(self):
		self.assertIsNone(auth.hook())
		self.frappe.throw.assert_not_called()

	def test_service_account_cannot_reach_other_routes_or_override_dispatch(self):
		cases = [
			("/api/resource/User", "GET", None),
			("/api/method/press.api.site.archive", "POST", None),
			("/api/method/fodista_cloud_mcp", "POST", "frappe.client.delete"),
			("/", "POST", "fodista_cloud_mcp"),
			("/api/method/fodista_cloud_mcp", "GET", None),
		]
		for path, method, cmd in cases:
			with self.subTest(path=path, method=method, cmd=cmd):
				self.frappe.request.path = path
				self.frappe.request.method = method
				self.frappe.form_dict.cmd = cmd
				with self.assertRaises(PermissionError):
					auth.hook()

	def test_other_system_users_keep_existing_route_access(self):
		self.frappe.get_roles.return_value = ["System Manager"]
		self.frappe.request.path = "/api/resource/User"
		self.assertIsNone(auth.hook())
		self.frappe.throw.assert_not_called()

	def test_site_methods_reject_non_administrator_before_side_effects(self):
		from press.press.doctype.site import site as site_module

		self.frappe.session.data = SimpleNamespace(user_type="System User")
		with patch.object(site_module, "frappe", self.frappe), patch.object(site_module, "Agent") as agent:
			site = object.__new__(site_module.Site)
			for method, kwargs in [
				("archive", {}),
				("reinstall", {}),
				("retry_archive", {}),
				("cleanup_after_archive", {}),
				("forcefully_remove_site", {"bench": "unused"}),
			]:
				with self.subTest(method=method), self.assertRaises(PermissionError):
					getattr(site, method)(**kwargs)
			agent.assert_not_called()

	def test_document_delete_denies_system_users_and_keeps_other_permissions(self):
		from press import overrides

		self.frappe.db = SimpleNamespace(get_value=Mock(return_value="System User"))
		with patch.object(overrides, "frappe", self.frappe):
			doc = SimpleNamespace(doctype="Site")
			self.assertFalse(overrides.has_permission(doc, "delete", "manager@example.com"))
			self.assertTrue(overrides.has_permission(doc, "delete", "Administrator"))
			self.assertTrue(overrides.has_permission(doc, "write", "manager@example.com"))

	def test_raw_document_delete_hook_is_registered(self):
		from press import hooks

		self.assertEqual(hooks.doc_events["Site"]["on_trash"], "press.site_access.require_site_administrator")
