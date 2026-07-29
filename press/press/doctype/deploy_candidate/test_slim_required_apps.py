# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

import unittest
from unittest.mock import Mock, patch

import frappe

from press.press.doctype.deploy_candidate.validations import PreBuildValidations


class TestSlimRequiredApps(unittest.TestCase):
	@patch(
		"press.press.doctype.deploy_candidate.validations.frappe.get_all",
		return_value=["console_agent"],
	)
	def test_required_app_cannot_be_excluded_from_runtime_image(self, get_all):
		candidate = Mock(
			apply_new_build=1,
			build_runtime_image=1,
			apps=[
				frappe._dict(app="fodista", app_name="fodista"),
				frappe._dict(app="console_agent", app_name="console_agent"),
			],
		)
		candidate.has_app.return_value = True
		validator = PreBuildValidations(candidate, {})

		with self.assertRaisesRegex(Exception, "Required app excluded from slim image"):
			validator._check_required_apps(
				"fodista",
				["divic-tech/console_agent"],
				validator._get_slim_excluded_apps(),
			)

		get_all.assert_called_once_with(
			"App",
			{"exclude_from_slim_images": True},
			pluck="name",
		)

	@patch("press.press.doctype.deploy_candidate.validations.frappe.get_all")
	def test_legacy_build_does_not_query_slim_exclusions(self, get_all):
		candidate = Mock(
			apply_new_build=0,
			build_runtime_image=1,
			apps=[],
		)

		self.assertEqual(
			PreBuildValidations(candidate, {})._get_slim_excluded_apps(),
			set(),
		)
		get_all.assert_not_called()


if __name__ == "__main__":
	unittest.main()
