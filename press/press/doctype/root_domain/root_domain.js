// Copyright (c) 2021, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on('Root Domain', {
	refresh: function (frm) {
		frm.trigger('set_mandatory_fields');
		if (
			frm.doc.cloudflare_saas_enabled &&
			frappe.user.has_role('System Manager')
		) {
			frm.add_custom_button(
				__('Configure SaaS Routing'),
				() =>
					frm
						.call('setup_cloudflare_saas')
						.then(() =>
							frappe.show_alert(__('Cloudflare for SaaS configured.')),
						),
				__('Cloudflare'),
			);
		}
	},

	dns_provider: function (frm) {
		frm.trigger('set_mandatory_fields');
	},

	set_mandatory_fields: function (frm) {
		frm.set_df_property(
			'aws_access_key_id',
			'reqd',
			frm.doc.dns_provider === 'AWS Route 53',
		);
		frm.set_df_property(
			'aws_secret_access_key',
			'reqd',
			frm.doc.dns_provider === 'AWS Route 53',
		);
		frm.set_df_property(
			'cloudflare_zone_id',
			'reqd',
			frm.doc.dns_provider === 'Cloudflare',
		);
	},
});
